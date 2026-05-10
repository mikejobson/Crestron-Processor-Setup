"""SSH and SFTP operations for Crestron processors via paramiko.

Crestron processors run a custom CLI shell (not a standard Unix shell).
We must use paramiko's invoke_shell() with channel read/write and prompt
detection — exec_command() will not work.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path

import paramiko
from rich.console import Console
import httpx

# Regex matching the Crestron CLI prompt: MODEL> (e.g., CP4>, MC4>, TSW-1070>)
PROMPT_RE = re.compile(rb"([A-Za-z0-9][-A-Za-z0-9]*[A-Za-z0-9])>")
# Match the prompt at the end of output (possibly with trailing whitespace)
PROMPT_END_RE = re.compile(rb"([A-Za-z0-9][-A-Za-z0-9]*[A-Za-z0-9])>\s*$")

# Timeout waiting for prompt responses
DEFAULT_TIMEOUT = 15
CONNECT_TIMEOUT = 10


class CrestronSSH:
    """Manage an SSH shell session to a Crestron processor."""

    def __init__(self, host: str, username: str, password: str = "",
                 console: Console | None = None,
                 use_key_auth: bool = False):
        self.host = host
        self.username = username
        self.password = password
        self.console = console
        self.use_key_auth = use_key_auth
        self.client: paramiko.SSHClient | None = None
        self.channel: paramiko.Channel | None = None
        self.model: str = ""
        self._buffer = b""

    def connect(self, timeout: int = CONNECT_TIMEOUT) -> str:
        """Connect and detect the processor model from the prompt.

        If use_key_auth is True, tries SSH agent and key files first.
        Falls back to password authentication if key auth fails.
        Returns the model name (e.g., 'CP4', 'MC4').
        """
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        _connect_client(self.client, self.host, self.username, self.password,
                        timeout=timeout, use_key_auth=self.use_key_auth)
        self.channel = self.client.invoke_shell(width=200, height=50)
        self.channel.settimeout(DEFAULT_TIMEOUT)

        # Read until we get the initial prompt
        output = self._read_until_prompt(timeout=15)
        if self.model:
            return self.model
        # Try to extract from whatever we got
        m = PROMPT_RE.search(output)
        if m:
            self.model = m.group(1).decode()
        return self.model

    def send_command(self, command: str, timeout: int = DEFAULT_TIMEOUT,
                     label: str = "") -> str:
        """Send a CLI command and return the response text.

        Waits for the MODEL> prompt after the command output.
        """
        if not self.channel:
            raise RuntimeError("Not connected")

        if label and self.console:
            self.console.print(f"  --- {label} ---")

        self.channel.sendall(command.encode() + b"\r")
        raw = self._read_until_prompt(timeout=timeout)

        # Strip the echoed command from the start and the prompt from the end
        text = raw.decode("ascii", errors="ignore")
        # Remove the echoed command line
        lines = text.splitlines()
        if lines and command.strip().lower() in lines[0].strip().lower():
            lines = lines[1:]
        # Remove trailing prompt line
        if lines and PROMPT_RE.search(lines[-1].encode()):
            lines = lines[:-1]

        response = "\n".join(lines).strip()
        if self.console and response:
            self.console.print(f"    {response}")
        return response

    def disconnect(self) -> None:
        """Send BYE and close the connection."""
        if self.channel:
            try:
                self.channel.sendall(b"BYE\r")
                time.sleep(0.5)
            except Exception:
                pass
        if self.channel:
            try:
                self.channel.close()
            except Exception:
                pass
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
        self.channel = None
        self.client = None

    def _read_until_prompt(self, timeout: int = DEFAULT_TIMEOUT) -> bytes:
        """Read channel output until a MODEL> prompt is found."""
        if not self.channel:
            raise RuntimeError("Not connected")

        deadline = time.time() + timeout
        buf = b""

        while time.time() < deadline:
            if self.channel.recv_ready():
                chunk = self.channel.recv(4096)
                if not chunk:
                    break
                buf += chunk
                # Check for prompt at end of buffer
                m = PROMPT_END_RE.search(buf)
                if m:
                    self.model = m.group(1).decode()
                    return buf
            else:
                time.sleep(0.1)

        return buf

    def __enter__(self) -> CrestronSSH:
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.disconnect()


class CrestronFirstBoot:
    """Handle the first-boot account creation flow.

    On first boot, Crestron processors accept SSH as 'crestron' with an
    empty password, then immediately prompt for Username:/Password:/Verify
    to create the initial admin account.
    """

    @staticmethod
    def try_create_account(host: str, new_user: str, new_pass: str,
                           console: Console | None = None) -> bool:
        """Attempt first-boot account creation.

        Returns True if account was created successfully.
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                host, username="crestron", password="",
                timeout=CONNECT_TIMEOUT, look_for_keys=False, allow_agent=False,
            )
        except (paramiko.AuthenticationException, paramiko.SSHException, OSError):
            return False

        channel = client.invoke_shell(width=200, height=50)
        channel.settimeout(30)

        try:
            output = _read_until(channel, [b"Username:", b">"], timeout=15)
            if b"Username:" not in output:
                # Got a regular prompt — not first boot
                channel.close()
                client.close()
                return False

            # Send new username
            channel.sendall(new_user.encode() + b"\r")
            _read_until(channel, [b"Password:"], timeout=10)

            # Send new password
            channel.sendall(new_pass.encode() + b"\r")
            _read_until(channel, [b"Verify password:", b"Verify Password:"], timeout=10)

            # Confirm password
            channel.sendall(new_pass.encode() + b"\r")
            result = _read_until(channel, [b"successfully", b"error", b">"], timeout=15)

            success = b"successfully" in result.lower()
            if success and console:
                console.print(f"[green][OK][/green] Admin account '{new_user}' created.")
            return success
        except Exception:
            return False
        finally:
            try:
                channel.close()
            except Exception:
                pass
            client.close()

    @staticmethod
    def check_first_boot(host: str) -> bool:
        """Quick check whether a processor is in first-boot state.

        First tries HTTPS — on first boot the web UI redirects to
        /createUser.html. Falls back to SSH as crestron/empty password
        and looks for the Username: prompt.
        """
        # Fast path: check the web UI for the first-boot page
        if _check_first_boot_https(host):
            return True

        # Slow path: try SSH with default credentials
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                host, username="crestron", password="",
                timeout=5, look_for_keys=False, allow_agent=False,
            )
        except (paramiko.AuthenticationException, paramiko.SSHException, OSError):
            return False

        try:
            channel = client.invoke_shell(width=200, height=50)
            channel.settimeout(5)
            output = _read_until(channel, [b"Username:", b">"], timeout=5)
            is_first_boot = b"Username:" in output
            channel.close()
            return is_first_boot
        except Exception:
            return False
        finally:
            client.close()


def _check_first_boot_https(host: str) -> bool:
    """Check if the web UI redirects to /createUser.html (first-boot indicator)."""
    try:
        resp = httpx.get(
            f"https://{host}/",
            verify=False,
            timeout=5,
            follow_redirects=True,
        )
        return "createUser" in str(resp.url) or "createUser" in resp.text
    except Exception:
        return False


def _read_until(channel: paramiko.Channel, markers: list[bytes],
                timeout: int = 10) -> bytes:
    """Read from channel until one of the marker strings is found."""
    deadline = time.time() + timeout
    buf = b""
    markers_lower = [m.lower() for m in markers]

    while time.time() < deadline:
        if channel.recv_ready():
            chunk = channel.recv(4096)
            if not chunk:
                break
            buf += chunk
            buf_lower = buf.lower()
            if any(m in buf_lower for m in markers_lower):
                return buf
        else:
            time.sleep(0.1)
    return buf


def _detect_agent_socket() -> str | None:
    """Detect the SSH agent socket, checking ~/.ssh/config IdentityAgent.

    Paramiko only reads SSH_AUTH_SOCK, but many tools (1Password, Secretive)
    configure their agent via IdentityAgent in ~/.ssh/config.  We parse that
    directive and return the socket path if it exists.
    """
    ssh_config_path = Path.home() / ".ssh" / "config"
    if not ssh_config_path.exists():
        return None

    try:
        text = ssh_config_path.read_text(errors="ignore")
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("identityagent"):
                # IdentityAgent "~/Library/..." or IdentityAgent ~/Library/...
                parts = stripped.split(None, 1)
                if len(parts) < 2:
                    continue
                sock = parts[1].strip('"').strip("'")
                sock = os.path.expanduser(sock)
                if os.path.exists(sock):
                    return sock
    except Exception:
        pass
    return None


def _connect_client(
    client: paramiko.SSHClient,
    host: str,
    username: str,
    password: str = "",
    timeout: int = CONNECT_TIMEOUT,
    use_key_auth: bool = False,
) -> None:
    """Connect a paramiko SSHClient, trying key auth first if enabled.

    When use_key_auth is True, detects custom SSH agent sockets (e.g.
    1Password, Secretive) from ~/.ssh/config IdentityAgent directive,
    then tries agent + key file auth before falling back to password.
    """
    if use_key_auth:
        # Detect custom agent sockets (1Password, Secretive, etc.)
        custom_sock = _detect_agent_socket()
        old_sock = os.environ.get("SSH_AUTH_SOCK", "")
        if custom_sock:
            os.environ["SSH_AUTH_SOCK"] = custom_sock

        try:
            client.connect(
                host, username=username, timeout=timeout,
                look_for_keys=True, allow_agent=True,
            )
            return
        except (paramiko.AuthenticationException, Exception):
            pass  # Fall through to password auth
        finally:
            if custom_sock:
                os.environ["SSH_AUTH_SOCK"] = old_sock

    client.connect(
        host, username=username, password=password,
        timeout=timeout, look_for_keys=False, allow_agent=False,
    )


def sftp_upload(host: str, username: str, password: str,
                local_path: str, remote_dir: str,
                console: Console | None = None,
                use_key_auth: bool = False) -> bool:
    """Upload a file via SFTP to the processor.

    Returns True on success.
    """
    local = Path(local_path).expanduser()
    if not local.exists():
        if console:
            console.print(f"[red][FAIL][/red] Local file not found: {local}")
        return False

    remote_path = f"{remote_dir}/{local.name}"
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        _connect_client(client, host, username, password,
                        use_key_auth=use_key_auth)
        sftp = client.open_sftp()

        if console:
            console.print(f"  Uploading {local.name} → {remote_path}")

        sftp.put(str(local), remote_path)
        sftp.close()

        if console:
            console.print(f"[green][OK][/green] Upload complete: {local.name}")
        return True
    except Exception as e:
        if console:
            console.print(f"[red][FAIL][/red] SFTP upload failed: {e}")
        return False
    finally:
        client.close()


def check_ssh_ready(host: str, username: str, password: str,
                    timeout: int = 5,
                    use_key_auth: bool = False) -> bool:
    """Quick check if SSH is accepting connections and login works."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        _connect_client(client, host, username, password,
                        timeout=timeout, use_key_auth=use_key_auth)
        client.close()
        return True
    except Exception:
        return False


def sftp_download(host: str, username: str, password: str,
                  remote_path: str, local_dir: str,
                  console: Console | None = None,
                  use_key_auth: bool = False) -> Path | None:
    """Download a file via SFTP from the processor.

    Returns the local Path on success, or None on failure.
    """
    local_dest = Path(local_dir).expanduser()
    local_dest.mkdir(parents=True, exist_ok=True)
    filename = remote_path.rstrip("/").split("/")[-1]
    local_file = local_dest / filename

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        _connect_client(client, host, username, password,
                        use_key_auth=use_key_auth)
        sftp = client.open_sftp()

        if console:
            console.print(f"  Downloading {remote_path} → {local_file}")

        sftp.get(remote_path, str(local_file))
        sftp.close()

        if console:
            console.print(f"[green][OK][/green] Downloaded: {filename}")
        return local_file
    except Exception as e:
        if console:
            console.print(f"[red][FAIL][/red] SFTP download failed: {e}")
        return None
    finally:
        client.close()

