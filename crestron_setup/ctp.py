"""CTP (Crestron Transport Protocol) client for UC Engines.

UC Engines don't expose SSH — they use CTP over TLS on port 41797 for console
access and file transfers.  This module provides ``CrestronCTP``, which mirrors
the ``CrestronSSH`` API (connect / send_command / disconnect) so it can be used
as a drop-in replacement for IP table management and other console operations.

File uploads use the XMODEM-1K CRC protocol.  General file transfers are
triggered by ``XPUTFILE``, while project deployment uses ``PUTDISPLAY`` which
combines XMODEM upload with automatic extraction and activation.
"""

from __future__ import annotations

import os
import re
import socket
import ssl
import struct
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from rich.console import Console

# Reuse prompt regexes from ssh.py
PROMPT_RE = re.compile(rb"([A-Za-z0-9][-A-Za-z0-9]*[A-Za-z0-9])>")
PROMPT_END_RE = re.compile(rb"([A-Za-z0-9][-A-Za-z0-9]*[A-Za-z0-9])>\s*$")

# CTP default port (secure / TLS)
CTP_PORT = 41797

# Timeouts
DEFAULT_TIMEOUT = 15
CONNECT_TIMEOUT = 10

# XMODEM constants
_SOH = 0x01   # 128-byte data block
_STX = 0x02   # 1024-byte data block
_EOT = 0x04   # End of transmission
_ACK = 0x06   # Acknowledged
_NAK = 0x15   # Not acknowledged
_CAN = 0x18   # Cancel
_SUB = 0x1A   # Padding byte

_XMODEM_BLOCK_SIZE = 1024
_XMODEM_MAX_RETRIES = 10


def _crc16_xmodem(data: bytes) -> int:
    """Calculate XMODEM CRC-16 (polynomial 0x1021)."""
    crc = 0
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


class CrestronCTP:
    """Manage a CTP/TLS console session to a Crestron UC Engine."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str = "",
        console: Console | None = None,
        port: int = CTP_PORT,
    ):
        self.host = host
        self.username = username
        self.password = password
        self.console = console
        self.port = port
        self._sock: ssl.SSLSocket | None = None
        self.model: str = ""

    # ------------------------------------------------------------------ #
    #  Connection lifecycle
    # ------------------------------------------------------------------ #

    def connect(self, timeout: int = CONNECT_TIMEOUT) -> str:
        """Connect over TLS, authenticate, and detect the device model.

        Returns the model string (e.g. ``'UC-ENGINE'``).
        """
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw.settimeout(timeout)
        raw.connect((self.host, self.port))
        self._sock = ctx.wrap_socket(raw, server_hostname=self.host)

        # Wake the console and wait for Login: prompt
        self._send(b"\r\n")
        self._read_until([b"Login:"], timeout=10)

        # Send username
        self._send(self.username.encode() + b"\r\n")
        self._read_until([b"Password:"], timeout=10)

        # Send password
        self._send(self.password.encode() + b"\r\n")
        buf = self._read_until_prompt(timeout=15)

        m = PROMPT_RE.search(buf)
        if m:
            self.model = m.group(1).decode()
        return self.model

    def send_command(
        self,
        command: str,
        timeout: int = DEFAULT_TIMEOUT,
        label: str = "",
    ) -> str:
        """Send a CLI command and return the response text.

        Waits for the ``MODEL>`` prompt after the command output.
        """
        if not self._sock:
            raise RuntimeError("Not connected")

        if label and self.console:
            self.console.print(f"  --- {label} ---")

        self._send(command.encode() + b"\r\n")
        raw = self._read_until_prompt(timeout=timeout)

        text = raw.decode("ascii", errors="ignore")
        lines = text.splitlines()
        # Strip echoed command
        if lines and command.strip().lower() in lines[0].strip().lower():
            lines = lines[1:]
        # Strip trailing prompt
        if lines and PROMPT_RE.search(lines[-1].encode()):
            lines = lines[:-1]

        response = "\n".join(lines).strip()
        if self.console and response:
            self.console.print(f"    {response}")
        return response

    def disconnect(self) -> None:
        """Send BYE and close the TLS connection."""
        if self._sock:
            try:
                self._send(b"BYE\r\n")
                time.sleep(0.5)
            except Exception:
                pass
            try:
                self._sock.close()
            except Exception:
                pass
        self._sock = None

    # ------------------------------------------------------------------ #
    #  File upload via XMODEM-1K CRC
    # ------------------------------------------------------------------ #

    def xmodem_upload(
        self,
        local_path: str | Path,
        remote_name: str | None = None,
        remote_dir: str = "\\Display",
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> bool:
        """Upload a file to the device using XPUTFILE + XMODEM-1K CRC.

        Args:
            local_path: Path to the local file to upload.
            remote_name: Filename on the device (defaults to local name).
            remote_dir: Remote directory to CD into before upload.
            progress_callback: Called with ``(bytes_sent, total_bytes)``
                after each acknowledged block.

        Returns True on success.
        """
        if not self._sock:
            raise RuntimeError("Not connected")

        local = Path(local_path).expanduser()
        if not local.exists():
            raise FileNotFoundError(f"Local file not found: {local}")

        if remote_name is None:
            remote_name = local.name

        file_size = local.stat().st_size
        file_mtime = datetime.fromtimestamp(local.stat().st_mtime)
        date_str = file_mtime.strftime("%m-%d-%y")
        time_str = file_mtime.strftime("%H:%M:%S")

        # CD to target directory
        if remote_dir:
            self.send_command(f"CD {remote_dir}")

        # Send XPUT command
        xput_cmd = f"XPUT {file_size} {date_str} {time_str} {remote_name}\r\n"
        self._send(xput_cmd.encode())

        # Wait for 'C' — XMODEM-CRC ready signal
        if not self._wait_for_xmodem_start(timeout=15):
            raise RuntimeError("Device did not enter XMODEM receive mode")

        self._xmodem_send_file(local, progress_callback)
        self._read_until_prompt(timeout=10)
        return True

    def upload_project(
        self,
        ch5z_path: str | Path,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> bool:
        """Upload a CH5Z project and deploy it on the UC Engine.

        Uses the ``PUTDISPLAY`` command which combines XMODEM upload with
        automatic project extraction and activation — this is the same
        mechanism Crestron Toolbox uses.  The device shows "Loading Project"
        during transfer and "Extracting Project" once complete.

        Unlike ``XPUTFILE`` + ``SELECTPROJECT``, ``PUTDISPLAY`` properly
        triggers the on-device UI feedback and reliably updates the project.
        """
        if not self._sock:
            raise RuntimeError("Not connected")

        local = Path(ch5z_path).expanduser()
        if not local.exists():
            raise FileNotFoundError(f"Local file not found: {local}")

        # PUTDISPLAY takes no arguments — just triggers XMODEM receive
        self._send(b"PUTDISPLAY\r\n")

        if not self._wait_for_xmodem_start(timeout=15):
            raise RuntimeError("Device did not enter XMODEM receive mode")

        self._xmodem_send_file(local, progress_callback)

        # PUTDISPLAY responds with "Transfer successful." then a prompt
        buf = self._read_until_prompt(timeout=60)
        resp = buf.decode("ascii", errors="ignore")
        if "transfer successful" not in resp.lower():
            raise RuntimeError(f"Unexpected PUTDISPLAY response: {resp.strip()}")
        return True

    def _xmodem_send_file(
        self,
        local: Path,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> None:
        """Send a file over an active XMODEM-1K CRC session.

        The last block is padded with ``\\x00`` (not the traditional ``SUB``
        / ``0x1A``) so that binary payloads like ZIP archives are not
        corrupted by trailing padding bytes.
        """
        file_data = local.read_bytes()

        block_num = 1
        offset = 0
        retries = 0

        while offset < len(file_data):
            chunk = file_data[offset:offset + _XMODEM_BLOCK_SIZE]
            if len(chunk) < _XMODEM_BLOCK_SIZE:
                # Null-pad to preserve binary integrity (ZIP end-of-central-dir)
                chunk += b"\x00" * (_XMODEM_BLOCK_SIZE - len(chunk))

            crc = _crc16_xmodem(chunk)
            seq = block_num & 0xFF
            packet = (
                bytes([_STX, seq, 0xFF - seq])
                + chunk
                + struct.pack(">H", crc)
            )

            self._sock.send(packet)

            resp = self._recv_byte(timeout=10)
            if resp == _ACK:
                offset += _XMODEM_BLOCK_SIZE
                block_num += 1
                retries = 0
                if progress_callback:
                    progress_callback(min(offset, len(file_data)), len(file_data))
            elif resp == _NAK:
                retries += 1
                if retries > _XMODEM_MAX_RETRIES:
                    raise RuntimeError(
                        f"XMODEM transfer failed: too many NAKs at block {block_num}"
                    )
            elif resp == _CAN:
                raise RuntimeError("XMODEM transfer cancelled by device")
            else:
                retries += 1
                if retries > _XMODEM_MAX_RETRIES:
                    raise RuntimeError(
                        f"XMODEM transfer failed: unexpected response 0x{resp:02x}"
                    )

        self._sock.send(bytes([_EOT]))

    # ------------------------------------------------------------------ #
    #  Low-level I/O helpers
    # ------------------------------------------------------------------ #

    def _send(self, data: bytes) -> None:
        if not self._sock:
            raise RuntimeError("Not connected")
        self._sock.send(data)

    def _recv_all(self, timeout: float = 3.0) -> bytes:
        """Read all available data within *timeout* seconds."""
        if not self._sock:
            raise RuntimeError("Not connected")
        buf = b""
        self._sock.settimeout(timeout)
        while True:
            try:
                chunk = self._sock.recv(4096)
                if not chunk:
                    break
                buf += chunk
            except (socket.timeout, ssl.SSLError):
                break
        return buf

    def _recv_byte(self, timeout: float = 10.0) -> int:
        """Read exactly one byte, returning its integer value."""
        if not self._sock:
            raise RuntimeError("Not connected")
        self._sock.settimeout(timeout)
        data = self._sock.recv(1)
        if not data:
            raise RuntimeError("Connection closed")
        return data[0]

    def _read_until(self, markers: list[bytes], timeout: int = 10) -> bytes:
        """Read until one of the marker bytestrings appears."""
        if not self._sock:
            raise RuntimeError("Not connected")
        deadline = time.time() + timeout
        buf = b""
        markers_lower = [m.lower() for m in markers]
        while time.time() < deadline:
            remaining = max(0.1, deadline - time.time())
            self._sock.settimeout(remaining)
            try:
                chunk = self._sock.recv(4096)
                if not chunk:
                    break
                buf += chunk
                buf_lower = buf.lower()
                if any(m in buf_lower for m in markers_lower):
                    return buf
            except (socket.timeout, ssl.SSLError):
                break
        return buf

    def _read_until_prompt(self, timeout: int = DEFAULT_TIMEOUT) -> bytes:
        """Read until a ``MODEL>`` prompt is detected."""
        if not self._sock:
            raise RuntimeError("Not connected")
        deadline = time.time() + timeout
        buf = b""
        while time.time() < deadline:
            remaining = max(0.1, deadline - time.time())
            self._sock.settimeout(remaining)
            try:
                chunk = self._sock.recv(4096)
                if not chunk:
                    break
                buf += chunk
                m = PROMPT_END_RE.search(buf)
                if m:
                    self.model = m.group(1).decode()
                    return buf
            except (socket.timeout, ssl.SSLError):
                break
        return buf

    def _wait_for_xmodem_start(self, timeout: int = 15) -> bool:
        """Wait for the receiver to send ``C`` (CRC mode ready)."""
        if not self._sock:
            return False
        deadline = time.time() + timeout
        while time.time() < deadline:
            remaining = max(0.1, deadline - time.time())
            self._sock.settimeout(remaining)
            try:
                b = self._sock.recv(1)
                if b == b"C":
                    return True
            except (socket.timeout, ssl.SSLError):
                break
        return False

    # ------------------------------------------------------------------ #
    #  Context manager
    # ------------------------------------------------------------------ #

    def __enter__(self) -> CrestronCTP:
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.disconnect()
