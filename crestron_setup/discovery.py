"""Crestron device discovery via CIP protocol (UDP port 41794)."""

from __future__ import annotations

import errno
import platform
import re
import socket
import subprocess
import time

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from .models import Config, Device

CIP_PORT = 41794


def _get_broadcast_addresses() -> list[str]:
    """Get broadcast addresses for all active network interfaces."""
    addresses: list[str] = []
    try:
        system = platform.system()
        if system == "Darwin":
            output = subprocess.check_output(["ifconfig"], text=True, timeout=5)
            addresses = re.findall(r"broadcast\s+(\d+\.\d+\.\d+\.\d+)", output)
        elif system == "Linux":
            output = subprocess.check_output(
                ["ip", "-4", "addr", "show"], text=True, timeout=5
            )
            addresses = re.findall(r"brd\s+(\d+\.\d+\.\d+\.\d+)", output)
        elif system == "Windows":
            # Windows: fall back to global broadcast
            pass
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        pass
    # Deduplicate while preserving order
    return list(dict.fromkeys(addresses))


def _send_broadcast(sock: socket.socket, packet: bytes) -> None:
    """Send a discovery packet to all available broadcast addresses."""
    sent = False
    # Send to per-interface broadcast addresses to cover all subnets
    for target in _get_broadcast_addresses():
        try:
            sock.sendto(packet, (target, CIP_PORT))
            sent = True
        except OSError:
            continue
    # Also try global broadcast (covers Windows and fallback cases)
    try:
        sock.sendto(packet, ("255.255.255.255", CIP_PORT))
        sent = True
    except OSError as e:
        if e.errno not in (errno.EADDRNOTAVAIL, errno.ENETUNREACH):
            raise
    if not sent:
        raise OSError(
            errno.EADDRNOTAVAIL,
            "No broadcast-capable network interfaces found. "
            "Check that you are connected to a network.",
        )


def build_discovery_packet() -> bytes:
    """Build a CIP discovery broadcast packet (266 bytes)."""
    header = b"\x14\x00\x00\x00\x01\x04\x00\x03\x00\x00"
    hostname = socket.gethostname().encode("ascii", errors="ignore")
    payload = header + hostname + b"\x00\x00"
    # Pad to 266 bytes
    return payload + b"\x00" * (266 - len(payload))


def _parse_response(data: bytes, ip: str) -> Device | None:
    """Parse a CIP discovery response into a Device."""
    # Valid responses start with 0x15 0x00
    if not data.startswith(b"\x15\x00"):
        return None

    text = data.decode("ascii", errors="ignore")

    # Extract hostname from null-terminated strings
    hostname = ""
    for part in data.split(b"\x00"):
        if re.fullmatch(rb"[A-Za-z0-9_-]{3,}", part):
            hostname = part.decode()
            break

    # Device type (e.g., TSW-1060, RMC4, CP4)
    dev_match = re.search(r"([A-Z0-9][-A-Z0-9]*[A-Z0-9]) \[v", text)
    model = dev_match.group(1) if dev_match else ""

    # Firmware version
    fw_match = re.search(r"\[v([0-9.]+)", text)
    firmware_version = fw_match.group(1) if fw_match else ""

    # MAC address (@E- prefix + 12 hex digits)
    mac_match = re.search(r"@E-([0-9a-fA-F]{12})", text)
    mac = ""
    if mac_match:
        raw = mac_match.group(1)
        mac = ":".join(raw[i : i + 2] for i in range(0, 12, 2))

    return Device(
        ip=ip,
        hostname=hostname,
        model=model,
        firmware_version=firmware_version,
        mac=mac,
    )


def _discovery_panel(spinner: Spinner, devices: list[Device], phase: str) -> Panel:
    """Build a live panel showing discovery progress."""
    table = Table.grid(padding=(0, 1))
    table.add_column(width=3)
    table.add_column()
    table.add_row(spinner, Text.from_markup(f"[bold cyan]{phase}[/bold cyan]"))
    if devices:
        table.add_row("", Text.from_markup(f"[dim]{len(devices)} device(s) found[/dim]"))
        for dev in devices:
            label = dev.ip
            if dev.hostname:
                label += f"  {dev.hostname}"
            if dev.model:
                label += f"  ({dev.model})"
            table.add_row("", Text.from_markup(f"  [green]✓[/green] {label}"))
    return Panel(table, title="[bold]Device Discovery[/bold]", border_style="cyan", padding=(1, 2))


def discover_devices(config: Config, console: Console | None = None) -> list[Device]:
    """Broadcast CIP discovery packets and collect responses.

    Requires root/admin privileges for UDP broadcast on port 41794.
    """
    timeout = config.discovery_timeout
    repeats = config.discovery_broadcast_count
    packet = build_discovery_packet()

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", CIP_PORT))
        sock.settimeout(0.5)  # short timeout for non-blocking recv loop
    except PermissionError:
        if console:
            console.print(
                "[red]Permission denied:[/red] Discovery requires elevated privileges.\n"
                "Run with [bold]sudo[/bold] on macOS/Linux or as Administrator on Windows."
            )
        return []
    except OSError as e:
        if console:
            console.print(f"[red]Network error:[/red] {e}")
        return []

    seen: set[tuple[str, str]] = set()
    devices: list[Device] = []
    spinner = Spinner("dots", style="cyan")

    if not console:
        # No console — run silently
        for _ in range(repeats):
            _send_broadcast(sock, packet)
            time.sleep(0.2)
        start = time.time()
        while time.time() - start < timeout:
            try:
                data, (ip, _) = sock.recvfrom(2048)
            except socket.timeout:
                break
            device = _parse_response(data, ip)
            if device and (device.ip, device.mac) not in seen:
                seen.add((device.ip, device.mac))
                devices.append(device)
        sock.close()
        return devices

    with Live(_discovery_panel(spinner, devices, "Broadcasting…"), console=console, refresh_per_second=10) as live:
        # Send discovery packets
        for i in range(repeats):
            _send_broadcast(sock, packet)
            time.sleep(0.2)

        # Collect responses
        start = time.time()
        while time.time() - start < timeout:
            try:
                data, (ip, _) = sock.recvfrom(2048)
            except socket.timeout:
                elapsed = time.time() - start
                remaining = max(0, timeout - elapsed)
                live.update(_discovery_panel(spinner, devices, f"Listening… {remaining:.0f}s remaining"))
                continue

            device = _parse_response(data, ip)
            if not device:
                continue

            key = (device.ip, device.mac)
            if key in seen:
                continue
            seen.add(key)
            devices.append(device)
            live.update(_discovery_panel(spinner, devices, f"Listening… {len(devices)} found"))

    sock.close()
    return devices


def _device_type_label(model: str) -> str:
    """Determine device type from model string for display."""
    upper = model.upper()
    if upper.startswith("UC-") or upper == "UC-ENGINE":
        return "UC Engine"
    if any(upper.startswith(p) for p in ("TSW-", "TS-", "TST-")):
        return "Touchpanel"
    return "Processor"


def print_device_table(devices: list[Device], console: Console) -> None:
    """Print a rich table of discovered devices."""
    table = Table(title="Discovered Crestron Devices")
    table.add_column("#", style="dim", width=3)
    table.add_column("IP Address", style="cyan")
    table.add_column("Hostname", style="green")
    table.add_column("Model", style="yellow")
    table.add_column("Type", style="dim")
    table.add_column("Firmware", style="magenta")
    table.add_column("MAC Address", style="dim")
    table.add_column("First Boot?", style="red")

    for i, dev in enumerate(devices, 1):
        fb = "Yes" if dev.is_first_boot else ""
        dev_type = _device_type_label(dev.model) if dev.model else ""
        table.add_row(
            str(i),
            dev.ip,
            dev.hostname,
            dev.model,
            dev_type,
            dev.firmware_version,
            dev.mac,
            fb,
        )

    console.print(table)
