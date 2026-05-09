"""Provisioning logic — 5-phase setup with animated progress tracking."""

from __future__ import annotations

import io
import logging
import os
import platform
import re
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from .firmware import find_local_firmware, version_compare
from .models import Config, Device
from .ssh import CrestronFirstBoot, CrestronSSH, check_ssh_ready, sftp_upload
from .timezones import timezone_label

PHASE_NAMES = [
    "Account Creation",
    "Public Key Upload",
    "Configure Processor",
    "Network Configuration",
    "Reboot",
    "Firmware Upload",
]


@contextmanager
def _quiet_ssh():
    """Suppress paramiko/cryptography/ssh logging and stderr noise."""
    loggers = ["paramiko", "paramiko.transport", "cryptography"]
    saved = {name: logging.getLogger(name).level for name in loggers}
    for name in loggers:
        logging.getLogger(name).setLevel(logging.CRITICAL)
    old_stderr = sys.stderr
    sys.stderr = io.StringIO()
    try:
        yield
    finally:
        sys.stderr = old_stderr
        for name, level in saved.items():
            logging.getLogger(name).setLevel(level)


class _StepTracker:
    """Tracks and renders provisioning step progress with animated spinners."""

    def __init__(self, device_label: str, phases: list[str]):
        self.device_label = device_label
        self.phases = phases
        self.statuses: list[str] = ["pending"] * len(phases)
        self.details: list[str] = [""] * len(phases)
        self._panel_title = f"Provisioning {self.device_label}"
        # Persist one spinner so the animation frame advances across renders
        self._spinner = Spinner("dots", style="cyan")

    def start(self, index: int, detail: str = "") -> None:
        self.statuses[index] = "active"
        self.details[index] = detail

    def ok(self, index: int, detail: str = "") -> None:
        self.statuses[index] = "ok"
        if detail:
            self.details[index] = detail

    def fail(self, index: int, detail: str = "") -> None:
        self.statuses[index] = "fail"
        if detail:
            self.details[index] = detail

    def skip(self, index: int, detail: str = "skipped") -> None:
        self.statuses[index] = "skip"
        self.details[index] = detail

    def render_static(self) -> Table:
        """Render the step list without spinners (for final display)."""
        return self._build_table(animated=False)

    def _build_table(self, animated: bool = True) -> Table:
        table = Table.grid(padding=(0, 1))
        table.add_column(width=3)
        table.add_column(width=3)
        table.add_column()

        for i, phase in enumerate(self.phases):
            status = self.statuses[i]
            detail = self.details[i]
            num = f"{i + 1}."
            detail_suffix = f"  [dim]{detail}[/dim]" if detail else ""

            if status == "active":
                icon: object = self._spinner if animated else "●"
                label: object = Text.from_markup(
                    f"[bold cyan]{phase}[/bold cyan]{detail_suffix}"
                )
            elif status == "ok":
                icon = Text.from_markup("[green]✓[/green]")
                label = Text.from_markup(f"{phase}{detail_suffix}")
            elif status == "fail":
                icon = Text.from_markup("[red]✗[/red]")
                label = Text.from_markup(f"[red]{phase}[/red]{detail_suffix}")
            elif status == "skip":
                icon = Text.from_markup("[dim]–[/dim]")
                label = Text.from_markup(f"[dim]{phase}{detail_suffix}[/dim]")
            else:
                icon = Text.from_markup("[dim]○[/dim]")
                label = Text.from_markup(f"[dim]{phase}[/dim]")

            table.add_row(icon, num, label)

        return table

    def __rich__(self) -> Panel:
        return Panel(
            self._build_table(animated=True),
            title=f"[bold]{self._panel_title}[/bold]",
            border_style="cyan",
            padding=(1, 2),
        )


def _clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def provision_device(
    device: Device,
    username: str,
    password: str,
    config: Config,
    console: Console,
    skip_firmware: bool = False,
    skip_reboot: bool = False,
) -> bool:
    """Run all 5 provisioning phases against a single device.

    Returns True if provisioning completed successfully.
    """
    host = device.ip or device.hostname
    tracker = _StepTracker(host, list(PHASE_NAMES))
    results: dict[str, str] = {"host": host, "username": username}

    _clear()
    success = _run_provisioning(
        host, device, username, password, config, console,
        tracker, results, skip_firmware, skip_reboot,
    )
    _show_results(console, tracker, results, success, config)
    return success


def _run_provisioning(
    host: str,
    device: Device,
    username: str,
    password: str,
    config: Config,
    console: Console,
    tracker: _StepTracker,
    results: dict[str, str],
    skip_firmware: bool,
    skip_reboot: bool,
) -> bool:
    """Execute all phases inside a Live display. Returns True on success."""
    model_name = ""
    current_puf_version = ""
    pubkey_path = Path(config.pubkey_file).expanduser()

    with Live(tracker, console=console, refresh_per_second=10) as live:

        # ── Phase 1: Account Creation ──────────────────────────────────
        tracker.start(0, "Checking credentials…")
        live.update(tracker)

        with _quiet_ssh():
            login_ok = not device.is_first_boot and _try_login(host, username, password)

        if not login_ok:
            tracker.details[0] = "Creating account…"
            live.update(tracker)
            with _quiet_ssh():
                created = CrestronFirstBoot.try_create_account(host, username, password)
            if created:
                tracker.ok(0, f"Account '{username}' created")
            elif _try_login(host, username, password):
                tracker.ok(0, f"Account '{username}' already exists")
            else:
                tracker.fail(0, "Cannot create account or log in")
                live.update(tracker)
                time.sleep(2)
                return False
        else:
            tracker.ok(0, f"Logged in as '{username}'")
        live.update(tracker)
        time.sleep(2)  # Let processor settle

        # ── Phase 2: Upload Public Key ─────────────────────────────────
        tracker.start(1, "Uploading…")
        live.update(tracker)

        if not pubkey_path.exists():
            tracker.skip(1, f"Key not found: {pubkey_path.name}")
        else:
            if sftp_upload(host, username, password, str(pubkey_path), "/user"):
                tracker.ok(1, pubkey_path.name)
            else:
                tracker.fail(1, "Upload failed")
                live.update(tracker)
                time.sleep(2)
                return False
        live.update(tracker)

        # ── Phase 3: Configure Processor ───────────────────────────────
        tracker.start(2, "Connecting…")
        live.update(tracker)

        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        current_date = now.strftime("%m-%d-%Y")

        commands: list[tuple[str, str]] = []
        pubkey_basename = pubkey_path.name if pubkey_path.exists() else ""
        if pubkey_basename:
            commands.append((
                f"ADDPUBKEYTOUSER -N:{username} -K:{pubkey_basename}",
                "Registering public key",
            ))
        commands += [
            (f"TIMEZONE {config.timezone}", "Setting timezone"),
            (f"TIMEDATE {current_time} {current_date}", "Setting date/time"),
            (f"SNTP SERVER:{config.ntp_server}", "Configuring NTP"),
            ("SNTP SYNC", "Syncing time"),
            (f"WEBPORT {config.web_port}", "Setting web port"),
            (f"SECUREWEBPORT {config.secure_web_port}", "Setting secure web port"),
            (f"SETUSERLOGINATTEMPTS {config.user_login_attempts}", "Login attempts"),
            (f"SETUSERLOCKOUTTIME {config.user_lockout_time}", "Lockout time"),
            (f"SETLOGINATTEMPTS {config.login_attempts}", "Console login attempts"),
            (f"SETLOCKOUTTIME {config.lockout_time}", "Console lockout time"),
            (f"FIPSMODE {config.fips_mode}", "Setting FIPS mode"),
        ]

        try:
            with CrestronSSH(host, username, password) as ssh:
                model_name = ssh.model
                results["model"] = model_name

                for i, (cmd, desc) in enumerate(commands):
                    tracker.details[2] = f"{desc} ({i + 1}/{len(commands)})"
                    live.update(tracker)
                    ssh.send_command(cmd)

                tracker.details[2] = "Reading version info…"
                live.update(tracker)
                ver_output = ssh.send_command("VER -V", timeout=20)

                for line in ver_output.splitlines():
                    if "PUF:" in line.upper() and "PUFEXEC" not in line.upper():
                        m = re.search(r"PUF:\s*([\d.]+)", line, re.IGNORECASE)
                        if m:
                            current_puf_version = m.group(1)
                            break

        except Exception as e:
            tracker.fail(2, str(e))
            live.update(tracker)
            time.sleep(2)
            return False

        detail = f"{len(commands)} settings applied"
        if model_name:
            device.model = model_name
            detail = f"{model_name} — {detail}"
        tracker.ok(2, detail)
        results["puf_version"] = current_puf_version
        live.update(tracker)

        # ── Phase 4: Network Configuration ─────────────────────────────
        net = device.network
        if not net:
            tracker.skip(3, "No changes requested")
            live.update(tracker)
        elif net.mode == "dhcp":
            tracker.start(3, "Enabling DHCP…")
            live.update(tracker)
            try:
                with CrestronSSH(host, username, password) as ssh:
                    ssh.send_command("DHCP 0 ON /now")
                    # Confirm via IPCONFIG
                    tracker.details[3] = "Verifying…"
                    live.update(tracker)
                    ip_output = ssh.send_command("IPCONFIG /ALL", timeout=10)
                    results["ip_config"] = ip_output
                tracker.ok(3, "DHCP enabled")
            except Exception as e:
                tracker.fail(3, str(e))
                live.update(tracker)
                time.sleep(2)
                return False
            live.update(tracker)
        else:
            tracker.start(3, "Setting static IP…")
            live.update(tracker)
            try:
                with CrestronSSH(host, username, password) as ssh:
                    # Set IP details first (without /now), then disable DHCP
                    # last with /now so all changes activate together.
                    net_cmds = [
                        (f"IPADDRESS 0 {net.ip_address}", f"IP → {net.ip_address}"),
                        (f"IPMASK 0 {net.subnet_mask}", f"Mask → {net.subnet_mask}"),
                        (f"DEFROUTER 0 {net.gateway}", f"Gateway → {net.gateway}"),
                    ]
                    total = len(net_cmds) + len(net.dns_servers) + 1  # +1 for DHCP OFF
                    for i, (cmd, desc) in enumerate(net_cmds):
                        tracker.details[3] = f"{desc} ({i + 1}/{total})"
                        live.update(tracker)
                        ssh.send_command(cmd)

                    for i, dns in enumerate(net.dns_servers):
                        tracker.details[3] = f"DNS → {dns} ({len(net_cmds) + i + 1}/{total})"
                        live.update(tracker)
                        ssh.send_command(f"ADDDNS {dns}")

                    # Disable DHCP last — activates all pending static settings
                    tracker.details[3] = f"Disabling DHCP ({total}/{total})"
                    live.update(tracker)
                    ssh.send_command("DHCP 0 OFF /now")

                    # Confirm via IPCONFIG
                    tracker.details[3] = "Verifying…"
                    live.update(tracker)
                    ip_output = ssh.send_command("IPCONFIG /ALL", timeout=10)
                    results["ip_config"] = ip_output

                # After static IP change the host may have moved
                if net.ip_address:
                    host = net.ip_address

                tracker.ok(3, f"{net.ip_address}/{net.subnet_mask}")
            except Exception as e:
                tracker.fail(3, str(e))
                live.update(tracker)
                time.sleep(2)
                return False
            live.update(tracker)

        # ── Phase 5: Reboot ────────────────────────────────────────────
        if skip_reboot:
            tracker.skip(4)
            live.update(tracker)
        else:
            tracker.start(4, "Sending reboot command…")
            live.update(tracker)

            try:
                with CrestronSSH(host, username, password) as ssh:
                    ssh.channel.sendall(b"REBOOT\r")  # type: ignore[union-attr]
                    time.sleep(1)
            except Exception:
                pass  # Connection drops immediately

            tracker.details[4] = "Waiting for processor to go offline…"
            live.update(tracker)
            min_wait = 30
            for sec in range(min_wait):
                tracker.details[4] = f"Rebooting… {min_wait - sec}s before first check"
                time.sleep(1)

            reboot_timeout = 300
            poll_interval = 5
            elapsed = 0
            came_back = False
            next_ping_at = 0  # ping immediately on first iteration
            ping_ok = False

            while elapsed < reboot_timeout:
                tracker.details[4] = (
                    f"Ping OK — checking SSH… {elapsed}s"
                    if ping_ok
                    else f"Waiting for response… {elapsed}s"
                )

                if elapsed >= next_ping_at:
                    ping_ok = _ping(host)
                    if ping_ok:
                        with _quiet_ssh():
                            if check_ssh_ready(host, username, password, timeout=5):
                                came_back = True
                                break
                    next_ping_at = elapsed + poll_interval

                time.sleep(1)
                elapsed += 1

            if came_back:
                tracker.ok(4, f"Back online after {elapsed}s")
            else:
                tracker.fail(4, f"Timed out after {reboot_timeout}s")
                live.update(tracker)
                time.sleep(2)
                return False
            live.update(tracker)

        # ── Phase 6: Firmware Upload ───────────────────────────────────
        if skip_firmware:
            tracker.skip(5)
            live.update(tracker)
        else:
            tracker.start(5, "Checking firmware…")
            live.update(tracker)

            if not model_name:
                tracker.skip(5, "No model detected")
            else:
                fw_path, fw_version = find_local_firmware(model_name, config)
                if not fw_path:
                    tracker.skip(5, "No firmware file found")
                elif current_puf_version and fw_version:
                    cmp = version_compare(fw_version, current_puf_version)
                    if cmp == 0:
                        tracker.ok(5, f"Already at v{fw_version}")
                    elif cmp < 0:
                        tracker.ok(
                            5,
                            f"Local v{fw_version} older than v{current_puf_version}",
                        )
                    else:
                        tracker.details[5] = f"Uploading {fw_path.name}…"
                        live.update(tracker)
                        if sftp_upload(
                            host, username, password, str(fw_path), "/firmware"
                        ):
                            tracker.details[5] = "Installing firmware…"
                            live.update(tracker)
                            try:
                                with _quiet_ssh():
                                    with CrestronSSH(host, username, password) as ssh:
                                        ssh.send_command("PUF", timeout=60)
                            except Exception:
                                pass  # PUF triggers reboot, connection drops
                            tracker.ok(5, f"Uploaded v{fw_version} — installing (device will reboot)")
                            results["firmware"] = fw_version
                        else:
                            tracker.fail(5, "Upload failed")
                else:
                    tracker.details[5] = f"Uploading {fw_path.name}…"
                    live.update(tracker)
                    if sftp_upload(
                        host, username, password, str(fw_path), "/firmware"
                    ):
                        tracker.details[5] = "Installing firmware…"
                        live.update(tracker)
                        try:
                            with _quiet_ssh():
                                with CrestronSSH(host, username, password) as ssh:
                                    ssh.send_command("PUF", timeout=60)
                        except Exception:
                            pass  # PUF triggers reboot, connection drops
                        tracker.ok(5, f"Uploaded {fw_path.name} — installing (device will reboot)")
                        results["firmware"] = fw_version or fw_path.name
                    else:
                        tracker.fail(5, "Upload failed")
            live.update(tracker)

        # Brief pause so user sees the completed tracker
        time.sleep(1)

    return all(s in ("ok", "skip") for s in tracker.statuses)


def _show_results(
    console: Console,
    tracker: _StepTracker,
    results: dict[str, str],
    success: bool,
    config: Config,
) -> None:
    """Clear screen and display a results summary panel."""
    _clear()

    if success:
        title = "[bold green]Provisioning Complete[/bold green]"
        border = "green"
    else:
        title = "[bold red]Provisioning Failed[/bold red]"
        border = "red"

    console.print(
        Panel(
            tracker.render_static(),
            title=title,
            border_style=border,
            padding=(1, 2),
        )
    )
    console.print()

    if success:
        info = Table.grid(padding=(0, 2))
        info.add_column(style="bold")
        info.add_column()

        host = results.get("host", "")
        model = results.get("model", "")
        info.add_row("Device:", f"{model} @ {host}" if model else host)
        info.add_row("Account:", results.get("username", ""))
        info.add_row("Timezone:", timezone_label(config.timezone))
        info.add_row("NTP Server:", config.ntp_server)
        info.add_row("Web Port:", str(config.web_port))
        info.add_row("Secure Port:", str(config.secure_web_port))
        info.add_row("FIPS Mode:", config.fips_mode)
        if results.get("puf_version"):
            info.add_row("PUF Version:", results["puf_version"])
        if results.get("firmware"):
            info.add_row("Firmware:", results["firmware"])
        if results.get("ip_config"):
            console.print(info)
            console.print()
            console.print("[bold]Network Configuration:[/bold]")
            console.print(results["ip_config"])
        else:
            console.print(info)
        console.print()


RESTORE_PHASE_NAMES = [
    "Initialize",
    "Reboot (1 of 2)",
    "Restore",
    "Reboot (2 of 2)",
]


def restore_device(
    device: Device,
    username: str,
    password: str,
    console: Console,
) -> bool:
    """Initialize and restore a device to factory defaults.

    Two-step process: initialize -y → reboot → restore -y → reboot → confirm ping.
    Returns True if the device comes back online after both reboots.
    """
    host = device.ip or device.hostname
    tracker = _StepTracker(host, list(RESTORE_PHASE_NAMES))
    tracker._panel_title = f"Restore & Erase {host}"

    _clear()
    success = _run_restore(host, username, password, console, tracker)
    _show_restore_results(console, tracker, host, success)
    return success


def _run_restore(
    host: str,
    username: str,
    password: str,
    console: Console,
    tracker: _StepTracker,
) -> bool:
    """Execute initialize/restore phases inside a Live display."""

    with Live(tracker, console=console, refresh_per_second=10) as live:

        # ── Phase 1: Initialize ────────────────────────────────────────
        tracker.start(0, "Connecting…")
        live.update(tracker)

        try:
            with _quiet_ssh():
                with CrestronSSH(host, username, password) as ssh:
                    tracker.details[0] = "Sending initialize command…"
                    live.update(tracker)
                    ssh.channel.sendall(b"initialize -y\r")  # type: ignore[union-attr]
                    time.sleep(2)
        except Exception as e:
            tracker.fail(0, str(e))
            live.update(tracker)
            time.sleep(2)
            return False

        tracker.ok(0, "Initialize command sent")
        live.update(tracker)

        # ── Phase 2: Reboot (1 of 2) ──────────────────────────────────
        tracker.start(1, "Waiting for processor to go offline…")
        live.update(tracker)

        if not _wait_for_reboot(host, username, password, tracker, 1, live):
            return False

        # ── Phase 3: Restore ──────────────────────────────────────────
        tracker.start(2, "Connecting…")
        live.update(tracker)

        try:
            with _quiet_ssh():
                with CrestronSSH(host, username, password) as ssh:
                    tracker.details[2] = "Sending restore command…"
                    live.update(tracker)
                    ssh.channel.sendall(b"restore -y\r")  # type: ignore[union-attr]
                    time.sleep(2)
        except Exception as e:
            tracker.fail(2, str(e))
            live.update(tracker)
            time.sleep(2)
            return False

        tracker.ok(2, "Restore command sent")
        live.update(tracker)

        # ── Phase 4: Reboot (2 of 2) ──────────────────────────────────
        tracker.start(3, "Waiting for processor to go offline…")
        live.update(tracker)

        if not _wait_for_reboot(host, username, password, tracker, 3, live, ping_only=True):
            return False

        time.sleep(1)

    return all(s in ("ok", "skip") for s in tracker.statuses)


def _wait_for_reboot(
    host: str,
    username: str,
    password: str,
    tracker: _StepTracker,
    phase: int,
    live: Live,
    ping_only: bool = False,
) -> bool:
    """Wait for a device to reboot and come back online.

    If ping_only is True, only wait for ping (device will be factory-reset
    so SSH credentials may no longer work).
    """
    min_wait = 30
    for sec in range(min_wait):
        tracker.details[phase] = f"Rebooting… {min_wait - sec}s before first check"
        live.update(tracker)
        time.sleep(1)

    reboot_timeout = 300
    poll_interval = 5
    elapsed = 0
    came_back = False
    next_ping_at = 0
    ping_ok = False

    while elapsed < reboot_timeout:
        if ping_only:
            tracker.details[phase] = (
                f"Ping OK — device online" if ping_ok
                else f"Waiting for response… {elapsed}s"
            )
        else:
            tracker.details[phase] = (
                f"Ping OK — checking SSH… {elapsed}s" if ping_ok
                else f"Waiting for response… {elapsed}s"
            )

        if elapsed >= next_ping_at:
            ping_ok = _ping(host)
            if ping_ok:
                if ping_only:
                    came_back = True
                    break
                with _quiet_ssh():
                    if check_ssh_ready(host, username, password, timeout=5):
                        came_back = True
                        break
            next_ping_at = elapsed + poll_interval

        live.update(tracker)
        time.sleep(1)
        elapsed += 1

    if came_back:
        tracker.ok(phase, f"Back online after {elapsed}s")
    else:
        tracker.fail(phase, f"Timed out after {reboot_timeout}s")
        live.update(tracker)
        time.sleep(2)
        return False
    live.update(tracker)
    return True


def _show_restore_results(
    console: Console,
    tracker: _StepTracker,
    host: str,
    success: bool,
) -> None:
    """Display restore results summary."""
    _clear()

    if success:
        title = "[bold green]Restore & Erase Complete[/bold green]"
        border = "green"
    else:
        title = "[bold red]Restore & Erase Failed[/bold red]"
        border = "red"

    console.print(
        Panel(
            tracker.render_static(),
            title=title,
            border_style=border,
            padding=(1, 2),
        )
    )
    console.print()

    if success:
        console.print(f"[green][OK][/green] {host} has been restored to factory defaults.")
        console.print("[dim]The device is now in first-boot mode.[/dim]")
    console.print()


def _try_login(host: str, username: str, password: str) -> bool:
    """Quick SSH login test."""
    return check_ssh_ready(host, username, password, timeout=5)


def _ping(host: str) -> bool:
    """Ping a host once. Cross-platform."""
    param = "-n" if platform.system() == "Windows" else "-c"
    timeout_param = "-w" if platform.system() == "Windows" else "-W"
    try:
        result = subprocess.run(
            ["ping", param, "1", timeout_param, "2", host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
