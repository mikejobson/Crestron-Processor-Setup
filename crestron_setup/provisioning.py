"""Provisioning logic — 5-phase setup with animated progress tracking."""

from __future__ import annotations

import io
import logging
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from .firmware import (
    _parse_puf_metadata,
    download_firmware_quiet,
    find_local_firmware,
    version_compare,
)
from .models import CommonSettings, Config, Device, resolve_profile, ResolvedProfile
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


def _resolve_pubkey(pubkey_file: str) -> Path | None:
    """Resolve a pubkey source (local path or URL) to a local file path.

    If pubkey_file looks like a URL (http/https), downloads the content to a
    temp file and returns that path. Otherwise treats it as a local path.
    Returns None if the key cannot be resolved.
    """
    parsed = urlparse(pubkey_file)
    if parsed.scheme in ("http", "https"):
        try:
            import httpx

            resp = httpx.get(pubkey_file, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            content = resp.text.strip()
            if not content:
                return None
            # Use first key line if multiple are returned (e.g. GitHub .keys)
            first_key = content.splitlines()[0]
            # Write to a named temp file that persists for the session
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".pub", prefix="crestron_key_", delete=False
            )
            tmp.write(first_key + "\n")
            tmp.close()
            return Path(tmp.name)
        except Exception:
            return None
    else:
        path = Path(pubkey_file).expanduser()
        return path if path.exists() else None


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


class _NullLive:
    """No-op replacement for rich.live.Live used in headless/parallel mode."""

    def update(self, _renderable=None) -> None:
        pass

    def __enter__(self) -> _NullLive:
        return self

    def __exit__(self, *_args: object) -> None:
        pass


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
    headless: bool = False,
    tracker: _StepTracker | None = None,
    dry_run: bool = False,
    profile_name: str | None = None,
) -> bool | tuple[bool, _StepTracker, dict[str, str]]:
    """Run all 5 provisioning phases against a single device.

    When dry_run=True, connects read-only to show what would change.
    When headless=True, returns (success, tracker, results) without displaying.
    Otherwise returns True/False and shows results on console.
    """
    host = device.ip or device.hostname
    if tracker is None:
        tracker = _StepTracker(host, list(PHASE_NAMES))
    if dry_run:
        tracker._panel_title = f"Provision (Dry Run) — {tracker.device_label}"
    results: dict[str, str] = {"host": host, "username": username}
    if profile_name:
        results["profile"] = profile_name

    resolved = resolve_profile(profile_name, config)

    if headless:
        success = _run_provisioning(
            host, device, username, password, resolved.config, console,
            tracker, results, skip_firmware, skip_reboot,
            headless=True, dry_run=dry_run,
            resolved=resolved,
        )
        return success, tracker, results

    _clear()
    success = _run_provisioning(
        host, device, username, password, resolved.config, console,
        tracker, results, skip_firmware, skip_reboot,
        dry_run=dry_run,
        resolved=resolved,
    )
    if dry_run:
        _show_dry_run_results(console, tracker, results, success, resolved.config,
                              resolved=resolved)
    else:
        _show_results(console, tracker, results, success, resolved.config,
                      resolved=resolved)
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
    headless: bool = False,
    dry_run: bool = False,
    resolved: ResolvedProfile | None = None,
) -> bool:
    """Execute all phases inside a Live display. Returns True on success."""
    pubkey_path = _resolve_pubkey(config.pubkey_file)
    # Track whether we downloaded the key (needs cleanup)
    _is_temp_key = pubkey_path is not None and str(pubkey_path).startswith(
        tempfile.gettempdir()
    )

    try:
        if dry_run:
            return _run_dry_run_inner(
                host, device, username, password, config, console,
                tracker, results, skip_firmware, skip_reboot, pubkey_path,
                headless=headless, resolved=resolved,
            )
        return _run_provisioning_inner(
            host, device, username, password, config, console,
            tracker, results, skip_firmware, skip_reboot, pubkey_path,
            headless=headless, resolved=resolved,
        )
    finally:
        if _is_temp_key and pubkey_path and pubkey_path.exists():
            pubkey_path.unlink()


def _run_provisioning_inner(
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
    pubkey_path: Path | None,
    headless: bool = False,
    resolved: ResolvedProfile | None = None,
) -> bool:
    """Execute all phases inside a Live display. Returns True on success."""
    model_name = ""
    current_puf_version = ""

    live_cm: Live | _NullLive = _NullLive() if headless else Live(tracker, console=console, refresh_per_second=10)
    with live_cm as live:

        # ── Phase 1: Account Creation ──────────────────────────────────
        tracker.start(0, "Checking credentials…")
        live.update(tracker)

        with _quiet_ssh():
            login_ok = not device.is_first_boot and _try_login(
                host, username, password, use_key_auth=config.ssh_key_auth)

        if not login_ok:
            tracker.details[0] = "Creating account…"
            live.update(tracker)
            with _quiet_ssh():
                created = CrestronFirstBoot.try_create_account(host, username, password)
            if created:
                tracker.ok(0, f"Account '{username}' created")
            elif _try_login(host, username, password, use_key_auth=config.ssh_key_auth):
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

        if not pubkey_path:
            tracker.skip(1, "Key not found")
        else:
            if sftp_upload(host, username, password, str(pubkey_path), "/user", use_key_auth=config.ssh_key_auth):
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
        skipped = resolved.skipped if resolved else set()
        pubkey_basename = pubkey_path.name if pubkey_path else ""
        if pubkey_basename and "pubkey_file" not in skipped:
            commands.append((
                f"ADDPUBKEYTOUSER -N:{username} -K:{pubkey_basename}",
                "Registering public key",
            ))

        # Build standard commands, skipping any excluded by the profile
        _standard_commands: list[tuple[str, str, str]] = [
            (f"TIMEZONE {config.timezone}", "Setting timezone", "timezone"),
            (f"TIMEDATE {current_time} {current_date}", "Setting date/time", ""),
            (f"SNTP SERVER:{config.ntp_server}", "Configuring NTP", "ntp_server"),
            ("SNTP SYNC", "Syncing time", ""),
            (f"WEBPORT {config.web_port}", "Setting web port", "web_port"),
            (f"SECUREWEBPORT {config.secure_web_port}", "Setting secure web port", "secure_web_port"),
            (f"SETUSERLOGINATTEMPTS {config.user_login_attempts}", "Login attempts", "user_login_attempts"),
            (f"SETUSERLOCKOUTTIME {config.user_lockout_time}", "Lockout time", "user_lockout_time"),
            (f"SETLOGINATTEMPTS {config.login_attempts}", "Console login attempts", "login_attempts"),
            (f"SETLOCKOUTTIME {config.lockout_time}", "Console lockout time", "lockout_time"),
            (f"FIPSMODE {config.fips_mode}", "Setting FIPS mode", "fips_mode"),
        ]
        for cmd, desc, field_name in _standard_commands:
            if field_name and field_name in skipped:
                continue
            commands.append((cmd, desc))

        # Append extra commands from profile
        if resolved and resolved.extra_commands:
            for ec in resolved.extra_commands:
                label = ec.label or ec.command
                commands.append((ec.command, label))

        try:
            with CrestronSSH(host, username, password, use_key_auth=config.ssh_key_auth) as ssh:
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
        if resolved and resolved.name != "default":
            detail += f" (profile: {resolved.name})"
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
                with CrestronSSH(host, username, password, use_key_auth=config.ssh_key_auth) as ssh:
                    if net.hostname:
                        ssh.send_command(f"HOSTNAME {net.hostname}")
                    ssh.send_command("DHCP 0 ON /now")
                    # Confirm via IPCONFIG
                    tracker.details[3] = "Verifying…"
                    live.update(tracker)
                    ip_output = ssh.send_command("IPCONFIG /ALL", timeout=10)
                    results["ip_config"] = ip_output
                detail = "DHCP enabled"
                if net.hostname:
                    detail += f" — hostname: {net.hostname}"
                tracker.ok(3, detail)
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
                with CrestronSSH(host, username, password, use_key_auth=config.ssh_key_auth) as ssh:
                    # Set IP details first (without /now), then disable DHCP
                    # last with /now so all changes activate together.
                    net_cmds = []
                    if net.hostname:
                        net_cmds.append((f"HOSTNAME {net.hostname}", f"Hostname → {net.hostname}"))
                    net_cmds += [
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
                with CrestronSSH(host, username, password, use_key_auth=config.ssh_key_auth) as ssh:
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
                            if check_ssh_ready(host, username, password, timeout=5, use_key_auth=config.ssh_key_auth):
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
                dl_msg = "No firmware file found"
                fw_path, fw_version = find_local_firmware(model_name, config)
                if not fw_path:
                    # Try downloading from configured URL
                    tracker.details[5] = "Downloading firmware…"
                    live.update(tracker)
                    fw_path, dl_msg = download_firmware_quiet(model_name, config)
                    if fw_path:
                        fw_version, _ = _parse_puf_metadata(fw_path)
                if not fw_path:
                    tracker.skip(5, dl_msg)
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
                            host, username, password, str(fw_path), "/firmware",
                            use_key_auth=config.ssh_key_auth,
                        ):
                            tracker.details[5] = "Installing firmware…"
                            live.update(tracker)
                            try:
                                with _quiet_ssh():
                                    with CrestronSSH(host, username, password, use_key_auth=config.ssh_key_auth) as ssh:
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
                        host, username, password, str(fw_path), "/firmware",
                        use_key_auth=config.ssh_key_auth,
                    ):
                        tracker.details[5] = "Installing firmware…"
                        live.update(tracker)
                        try:
                            with _quiet_ssh():
                                with CrestronSSH(host, username, password, use_key_auth=config.ssh_key_auth) as ssh:
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


def _run_dry_run_inner(
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
    pubkey_path: Path | None,
    headless: bool = False,
    resolved: ResolvedProfile | None = None,
) -> bool:
    """Execute a dry run: connect read-only, collect planned changes."""
    planned_commands: list[str] = []
    planned_uploads: list[str] = []
    current_puf_version = ""
    model_name = ""

    live_cm: Live | _NullLive = (
        _NullLive() if headless
        else Live(tracker, console=console, refresh_per_second=10)
    )
    with live_cm as live:

        # ── Phase 1: Check Connectivity ────────────────────────────────
        tracker.start(0, "Checking connectivity…")
        live.update(tracker)

        with _quiet_ssh():
            login_ok = not device.is_first_boot and _try_login(
                host, username, password, use_key_auth=config.ssh_key_auth,
            )

        if device.is_first_boot:
            tracker.skip(
                0,
                "First boot — account creation required before dry run",
            )
            for i in range(1, len(PHASE_NAMES)):
                tracker.skip(i)
            live.update(tracker)
            time.sleep(1)

            results["first_boot_skip"] = "true"
            return True
        elif login_ok:
            tracker.ok(0, f"Login OK as '{username}'")
        else:
            tracker.fail(0, "Cannot connect — verify credentials")
            live.update(tracker)
            time.sleep(2)
            return False
        live.update(tracker)

        # ── Phase 2: Verify Public Key ─────────────────────────────────
        tracker.start(1, "Checking key…")
        live.update(tracker)

        if not pubkey_path:
            tracker.skip(1, "Key not found — would skip")
        else:
            tracker.ok(1, f"Would upload {pubkey_path.name} → /user/")
            planned_uploads.append(f"{pubkey_path.name} → /user/{pubkey_path.name}")
        live.update(tracker)

        # ── Phase 3: Review Configuration ──────────────────────────────
        tracker.start(2, "Reading current config…")
        live.update(tracker)

        now = datetime.now()
        skipped = resolved.skipped if resolved else set()
        pubkey_basename = pubkey_path.name if pubkey_path else ""
        if pubkey_basename and "pubkey_file" not in skipped:
            planned_commands.append(
                f"ADDPUBKEYTOUSER -N:{username} -K:{pubkey_basename}"
            )

        # Build standard commands, respecting profile skips
        _standard_dry: list[tuple[str, str]] = [
            (f"TIMEZONE {config.timezone}", "timezone"),
            (f"TIMEDATE {now.strftime('%H:%M:%S')} {now.strftime('%m-%d-%Y')}", ""),
            (f"SNTP SERVER:{config.ntp_server}", "ntp_server"),
            ("SNTP SYNC", ""),
            (f"WEBPORT {config.web_port}", "web_port"),
            (f"SECUREWEBPORT {config.secure_web_port}", "secure_web_port"),
            (f"SETUSERLOGINATTEMPTS {config.user_login_attempts}", "user_login_attempts"),
            (f"SETUSERLOCKOUTTIME {config.user_lockout_time}", "user_lockout_time"),
            (f"SETLOGINATTEMPTS {config.login_attempts}", "login_attempts"),
            (f"SETLOCKOUTTIME {config.lockout_time}", "lockout_time"),
            (f"FIPSMODE {config.fips_mode}", "fips_mode"),
        ]
        for cmd, field_name in _standard_dry:
            if field_name and field_name in skipped:
                continue
            planned_commands.append(cmd)

        # Extra commands from profile
        if resolved and resolved.extra_commands:
            for ec in resolved.extra_commands:
                planned_commands.append(ec.command)
        cmd_count = len(planned_commands)

        # Connect read-only to gather current state
        if not device.is_first_boot and login_ok:
            try:
                with _quiet_ssh():
                    with CrestronSSH(host, username, password, use_key_auth=config.ssh_key_auth) as ssh:
                        model_name = ssh.model
                        results["model"] = model_name

                        tracker.details[2] = "Reading version…"
                        live.update(tracker)
                        ver_output = ssh.send_command("VER -V", timeout=20)

                        for line in ver_output.splitlines():
                            if (
                                "PUF:" in line.upper()
                                and "PUFEXEC" not in line.upper()
                            ):
                                m = re.search(
                                    r"PUF:\s*([\d.]+)", line, re.IGNORECASE
                                )
                                if m:
                                    current_puf_version = m.group(1)
                                    break

                        # Read current settings for comparison
                        read_cmds = [
                            ("TIMEZONE", "timezone"),
                            ("SNTP", "sntp"),
                            ("WEBPORT", "web_port"),
                            ("SECUREWEBPORT", "secure_web_port"),
                            ("HOSTNAME", "hostname"),
                            ("FIPSMODE", "fips_mode"),
                            ("SETUSERLOGINATTEMPTS", "user_login_attempts"),
                            ("SETUSERLOCKOUTTIME", "user_lockout_time"),
                            ("SETLOGINATTEMPTS", "login_attempts"),
                            ("SETLOCKOUTTIME", "lockout_time"),
                        ]
                        current_values: dict[str, str] = {}
                        for i, (cmd, key) in enumerate(read_cmds):
                            tracker.details[2] = (
                                f"Reading settings… ({i + 1}/{len(read_cmds)})"
                            )
                            live.update(tracker)
                            try:
                                resp = ssh.send_command(cmd, timeout=10)
                                current_values[key] = resp.strip()
                            except Exception:
                                current_values[key] = ""

                        results["current_values"] = "\n".join(
                            f"{k}={v}" for k, v in current_values.items()
                        )

                        tracker.details[2] = "Reading network config…"
                        live.update(tracker)
                        ip_output = ssh.send_command("IPCONFIG /ALL", timeout=10)
                        results["current_ipconfig"] = ip_output

                detail = f"{cmd_count} commands planned"
                if model_name:
                    device.model = model_name
                    detail = f"{model_name} — {detail}"
                if resolved and resolved.name != "default":
                    detail += f" (profile: {resolved.name})"
                tracker.ok(2, detail)
                results["puf_version"] = current_puf_version
            except Exception as e:
                tracker.fail(2, f"Cannot read config: {e}")
                live.update(tracker)
                time.sleep(2)
                return False
        else:
            tracker.ok(2, f"{cmd_count} commands planned")
        live.update(tracker)

        # ── Phase 4: Review Network ────────────────────────────────────
        net = device.network
        if not net:
            tracker.skip(3, "No changes requested")
        elif net.mode == "dhcp":
            if net.hostname:
                planned_commands.append(f"HOSTNAME {net.hostname}")
            planned_commands.append("DHCP 0 ON /now")
            detail = "Would enable DHCP"
            if net.hostname:
                detail += f" — hostname: {net.hostname}"
            tracker.ok(3, detail)
        else:
            if net.hostname:
                planned_commands.append(f"HOSTNAME {net.hostname}")
            planned_commands += [
                f"IPADDRESS 0 {net.ip_address}",
                f"IPMASK 0 {net.subnet_mask}",
                f"DEFROUTER 0 {net.gateway}",
            ]
            for dns in net.dns_servers:
                planned_commands.append(f"ADDDNS {dns}")
            planned_commands.append("DHCP 0 OFF /now")
            tracker.ok(3, f"Would set static IP {net.ip_address}/{net.subnet_mask}")
        live.update(tracker)

        # ── Phase 5: Reboot ────────────────────────────────────────────
        if skip_reboot:
            tracker.skip(4)
        else:
            planned_commands.append("REBOOT")
            tracker.ok(4, "Would reboot and wait for reconnect")
        live.update(tracker)

        # ── Phase 6: Firmware ──────────────────────────────────────────
        if skip_firmware:
            tracker.skip(5)
        else:
            tracker.start(5, "Checking firmware…")
            live.update(tracker)

            fw_model = model_name or device.model
            if not fw_model:
                tracker.skip(5, "No model detected")
            else:
                dl_msg = "No firmware available"
                fw_path, fw_version = find_local_firmware(fw_model, config)
                if not fw_path:
                    tracker.details[5] = "Checking download URL…"
                    live.update(tracker)
                    fw_path, dl_msg = download_firmware_quiet(fw_model, config)
                    if fw_path:
                        fw_version, _ = _parse_puf_metadata(fw_path)
                if not fw_path:
                    tracker.skip(5, dl_msg)
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
                        tracker.ok(
                            5,
                            f"Would upload v{fw_version} "
                            f"(current: v{current_puf_version})",
                        )
                        planned_uploads.append(
                            f"{fw_path.name} → /firmware/{fw_path.name}"
                        )
                        planned_commands.append("PUF")
                else:
                    tracker.ok(
                        5,
                        f"Would upload {fw_path.name} (cannot compare versions)",
                    )
                    planned_uploads.append(
                        f"{fw_path.name} → /firmware/{fw_path.name}"
                    )
                    planned_commands.append("PUF")
        live.update(tracker)

        time.sleep(1)

    results["planned_commands"] = "\n".join(planned_commands)
    results["planned_uploads"] = "\n".join(planned_uploads)

    return all(s in ("ok", "skip") for s in tracker.statuses)


def _show_results(
    console: Console,
    tracker: _StepTracker,
    results: dict[str, str],
    success: bool,
    config: Config,
    resolved: ResolvedProfile | None = None,
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
        if resolved and resolved.name != "default":
            info.add_row("Profile:", resolved.name)
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


def _compare_setting(current_response: str, planned_value: str,
                     compare_type: str) -> bool:
    """Smart comparison between a Crestron CLI response and a planned value.

    The CLI returns verbose human-readable strings (e.g., "Lockout timeout:
    1 minute") while config values are terse (e.g., "1m"). This function
    extracts the meaningful value from the response and compares it against
    the planned setting.
    """
    curr = current_response.strip().lower()
    plan = planned_value.strip().lower()
    if not curr:
        return False

    if compare_type == "port":
        # "Webserver port =  8080" or "Secure(SSL) Webserver port =  8443"
        m = re.search(r"(\d+)", curr)
        return m is not None and m.group(1) == plan

    if compare_type == "number":
        # "Maximum user login attempts allowed: 5" or "Maximum attempts allowed: 20"
        m = re.search(r"(\d+)\s*$", curr)
        if not m:
            # Try to find the number after a colon
            m = re.search(r":\s*(\d+)", curr)
        return m is not None and m.group(1) == plan

    if compare_type == "fips":
        # "FIPS mode: Disabled" → OFF, "FIPS mode: Enabled" → ON
        if "disabled" in curr or "off" in curr:
            return plan == "off"
        if "enabled" in curr or "on" in curr:
            return plan == "on"
        return plan in curr

    if compare_type == "duration":
        # "Lockout timeout: 1 minute" → "1m", "5 minutes" → "5m"
        # "Lockout timeout: 2 hours" → "2h"
        # Extract number and unit from response
        m = re.search(r"(\d+)\s*(minute|hour|min|hr)", curr)
        if m:
            num = m.group(1)
            unit = m.group(2)
            if unit.startswith("minute") or unit.startswith("min"):
                return plan == f"{num}m"
            if unit.startswith("hour") or unit.startswith("hr"):
                return plan == f"{num}h"
        # Fallback: check if planned value appears literally
        return plan in curr

    if compare_type == "sntp":
        # SNTP response is multi-line; check if the server address appears
        return plan in curr

    if compare_type == "timezone":
        # Timezone response may say "Daylight Time" while our label says
        # "Standard Time" depending on DST.  They represent the same zone.
        # Compare the timezone family name (before Daylight/Standard).
        curr_family = re.sub(
            r"\s*(daylight|standard)\s*time.*", "", curr
        ).strip()
        plan_family = re.sub(
            r"\s*(daylight|standard)\s*time.*", "", plan
        ).strip()
        if curr_family and plan_family:
            return curr_family == plan_family
        # Fallback: direct substring match
        return plan in curr

    # Default: substring match
    return plan in curr or curr == plan


def _show_dry_run_results(
    console: Console,
    tracker: _StepTracker,
    results: dict[str, str],
    success: bool,
    config: Config,
    resolved: ResolvedProfile | None = None,
) -> None:
    """Display dry-run summary showing current vs planned configuration."""
    _clear()

    title = "[bold cyan]Provision (Dry Run) Complete[/bold cyan]"
    border = "cyan"
    if not success:
        title = "[bold red]Provision (Dry Run) Failed[/bold red]"
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

    # Device info
    info = Table.grid(padding=(0, 2))
    info.add_column(style="bold")
    info.add_column()

    host = results.get("host", "")
    model = results.get("model", "")
    info.add_row("Device:", f"{model} @ {host}" if model else host)
    info.add_row("Account:", results.get("username", ""))
    if resolved and resolved.name != "default":
        info.add_row("Profile:", resolved.name)
    if results.get("puf_version"):
        info.add_row("Current PUF:", results["puf_version"])
    console.print(info)
    console.print()

    # First-boot devices can't be dry-run — need account creation first
    if results.get("first_boot_skip"):
        console.print(
            "[yellow][WARN][/yellow] This device is in first-boot mode. "
            "An admin account must be created before a dry run can read "
            "the current configuration.\n"
            "Run [bold]Provision[/bold] first to create the account, then "
            "use [bold]Provision (Dry Run)[/bold] to preview further changes."
        )
        console.print()
        console.print("[dim]No changes were made to the device.[/dim]")
        console.print()
        return

    # Parse current values read from device
    current_values: dict[str, str] = {}
    raw_cv = results.get("current_values", "")
    if raw_cv:
        for line in raw_cv.split("\n"):
            if "=" in line:
                k, v = line.split("=", 1)
                current_values[k] = v

    # Build configuration diff table with smart comparison
    skipped = resolved.skipped if resolved else set()
    diff_rows: list[tuple[str, str, str, str, str]] = [
        ("Timezone", current_values.get("timezone", ""),
         timezone_label(config.timezone), "timezone", "timezone"),
        ("NTP Server", current_values.get("sntp", ""),
         config.ntp_server, "sntp", "ntp_server"),
        ("Web Port", current_values.get("web_port", ""),
         str(config.web_port), "port", "web_port"),
        ("Secure Web Port", current_values.get("secure_web_port", ""),
         str(config.secure_web_port), "port", "secure_web_port"),
        ("FIPS Mode", current_values.get("fips_mode", ""),
         config.fips_mode, "fips", "fips_mode"),
        ("User Login Attempts", current_values.get("user_login_attempts", ""),
         str(config.user_login_attempts), "number", "user_login_attempts"),
        ("User Lockout Time", current_values.get("user_lockout_time", ""),
         config.user_lockout_time, "duration", "user_lockout_time"),
        ("Console Login Attempts", current_values.get("login_attempts", ""),
         str(config.login_attempts), "number", "login_attempts"),
        ("Console Lockout Time", current_values.get("lockout_time", ""),
         config.lockout_time, "duration", "lockout_time"),
    ]

    if current_values:
        diff_table = Table(
            title="Configuration Changes",
            border_style="cyan",
            show_lines=False,
        )
        diff_table.add_column("Setting", style="bold")
        diff_table.add_column("Current")
        diff_table.add_column("")
        diff_table.add_column("Planned")
        diff_table.add_column("")

        for label, current, planned, compare_type, field_name in diff_rows:
            if field_name in skipped:
                diff_table.add_row(
                    label,
                    f"[dim]{current}[/dim]" if current.strip() else "[dim]—[/dim]",
                    "",
                    "",
                    "[dim]skipped[/dim]",
                )
                continue

            matches = _compare_setting(current, planned, compare_type)
            if not current.strip():
                arrow = "→"
                status = ""
                current_display = "[dim]unknown[/dim]"
                planned_display = f"[yellow]{planned}[/yellow]"
            elif matches:
                arrow = ""
                status = "[dim]no change[/dim]"
                current_display = f"[dim]{current}[/dim]"
                planned_display = ""
            else:
                arrow = "→"
                status = "[yellow]changed[/yellow]"
                current_display = current
                planned_display = f"[yellow]{planned}[/yellow]"

            diff_table.add_row(
                label, current_display, arrow, planned_display, status,
            )

        console.print(diff_table)
        console.print()

    # Planned commands
    cmds = results.get("planned_commands", "")
    if cmds:
        cmd_table = Table(
            title="Commands to Execute",
            border_style="yellow",
            show_lines=False,
        )
        cmd_table.add_column("#", style="dim", width=4)
        cmd_table.add_column("Command")
        for i, cmd in enumerate(cmds.split("\n"), 1):
            cmd_table.add_row(str(i), cmd)
        console.print(cmd_table)
        console.print()

    # Planned uploads
    uploads = results.get("planned_uploads", "")
    if uploads:
        console.print("[bold]Files to Upload:[/bold]")
        for upload in uploads.split("\n"):
            console.print(f"  [yellow]↑[/yellow] {upload}")
        console.print()

    # Current network info
    ipconfig = results.get("current_ipconfig", "")
    if ipconfig:
        console.print("[bold]Current Network Configuration:[/bold]")
        console.print(ipconfig)
        console.print()

    console.print("[dim]No changes were made to the device.[/dim]")
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
    headless: bool = False,
    tracker: _StepTracker | None = None,
    use_key_auth: bool = False,
) -> bool | tuple[bool, _StepTracker]:
    """Initialize and restore a device to factory defaults.

    When headless=True, returns (success, tracker) without displaying.
    Otherwise returns True/False and shows results on console.
    """
    host = device.ip or device.hostname
    if tracker is None:
        tracker = _StepTracker(host, list(RESTORE_PHASE_NAMES))
        tracker._panel_title = f"Restore & Erase {host}"

    if headless:
        success = _run_restore(host, username, password, console, tracker,
                               headless=True, use_key_auth=use_key_auth)
        return success, tracker

    _clear()
    success = _run_restore(host, username, password, console, tracker,
                           use_key_auth=use_key_auth)
    _show_restore_results(console, tracker, host, success)
    return success


def _run_restore(
    host: str,
    username: str,
    password: str,
    console: Console,
    tracker: _StepTracker,
    headless: bool = False,
    use_key_auth: bool = False,
) -> bool:
    """Execute initialize/restore phases inside a Live display."""

    live_cm: Live | _NullLive = _NullLive() if headless else Live(tracker, console=console, refresh_per_second=10)
    with live_cm as live:

        # ── Phase 1: Initialize ────────────────────────────────────────
        tracker.start(0, "Connecting…")
        live.update(tracker)

        try:
            with _quiet_ssh():
                with CrestronSSH(host, username, password, use_key_auth=use_key_auth) as ssh:
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

        if not _wait_for_reboot(host, username, password, tracker, 1, live,
                                use_key_auth=use_key_auth):
            return False

        # ── Phase 3: Restore ──────────────────────────────────────────
        tracker.start(2, "Connecting…")
        live.update(tracker)

        try:
            with _quiet_ssh():
                with CrestronSSH(host, username, password, use_key_auth=use_key_auth) as ssh:
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

        if not _wait_for_reboot(host, username, password, tracker, 3, live,
                                ping_only=True, use_key_auth=use_key_auth):
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
    use_key_auth: bool = False,
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
                "Ping OK — device online" if ping_ok
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
                    if check_ssh_ready(host, username, password, timeout=5,
                                       use_key_auth=use_key_auth):
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


def _try_login(host: str, username: str, password: str,
               use_key_auth: bool = False) -> bool:
    """Quick SSH login test."""
    return check_ssh_ready(host, username, password, timeout=5,
                           use_key_auth=use_key_auth)


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


# --------------------------------------------------------------------------- #
#  Program Upload
# --------------------------------------------------------------------------- #

PROGRAM_PHASE_NAMES = [
    "Upload Program",
    "Load Program",
]


def upload_program(
    host: str,
    username: str,
    password: str,
    program_path: str,
    slot: int,
    console: Console,
    headless: bool = False,
    tracker: _StepTracker | None = None,
    use_key_auth: bool = False,
) -> bool | tuple[bool, _StepTracker]:
    """Upload a program file to a processor and load it.

    1. SFTP the file to /programXX/
    2. Run PROGLOAD -P:XX to load it

    When headless=True, returns (success, tracker) without displaying.
    Otherwise returns True/False.
    """
    if tracker is None:
        tracker = _StepTracker(host, list(PROGRAM_PHASE_NAMES))
        tracker._panel_title = f"Program Upload — {host}"

    slot_str = f"{slot:02d}"
    remote_dir = f"/program{slot_str}"
    local = Path(program_path).expanduser()

    live_cm: Live | _NullLive = _NullLive() if headless else Live(tracker, console=console, refresh_per_second=10)
    success = False
    with live_cm as live:
        # ── Phase 1: Upload ────────────────────────────────────────────
        tracker.start(0, f"Uploading {local.name}…")
        live.update(tracker)

        if not local.exists():
            tracker.fail(0, f"File not found: {local}")
            live.update(tracker)
        elif not sftp_upload(host, username, password, str(local), remote_dir, use_key_auth=use_key_auth):
            tracker.fail(0, "Upload failed")
            live.update(tracker)
        else:
            tracker.ok(0, f"{local.name} → {remote_dir}/")
            live.update(tracker)

            # ── Phase 2: Load ──────────────────────────────────────────
            tracker.start(1, f"Loading program in slot {slot_str}…")
            live.update(tracker)

            try:
                with CrestronSSH(host, username, password, use_key_auth=use_key_auth) as ssh:
                    ssh.send_command(f"PROGLOAD -P:{slot_str}", timeout=30)
                    tracker.ok(1, f"Slot {slot_str} loaded")
                    success = True
            except Exception as e:
                tracker.fail(1, str(e))
            live.update(tracker)

    if headless:
        return success, tracker

    if success:
        console.print()
        console.print(f"[green][OK][/green] Program uploaded and loaded in slot {slot_str}")
    return success


# --------------------------------------------------------------------------- #
#  Parallel Execution
# --------------------------------------------------------------------------- #

@dataclass
class DeviceResult:
    """Outcome of a parallel action on a single device."""
    device_label: str
    action: str
    success: bool
    tracker: _StepTracker
    results: dict[str, str] = field(default_factory=dict)


class _ParallelDisplay:
    """Combined live renderable showing per-step progress of all parallel actions."""

    def __init__(self, device_results: list[DeviceResult]) -> None:
        self._results = device_results
        self._spinner = Spinner("dots", style="cyan")

    def _step_icons(self, tracker: _StepTracker) -> Text:
        """Build a compact step progress line like: ✓ ✓ ● ○ ○ ○"""
        parts: list[tuple[str, str]] = []
        for i, s in enumerate(tracker.statuses):
            if s == "ok":
                parts.append(("✓", "green"))
            elif s == "fail":
                parts.append(("✗", "red"))
            elif s == "skip":
                parts.append(("–", "dim"))
            elif s == "active":
                parts.append(("●", "cyan bold"))
            else:
                parts.append(("○", "dim"))
        result = Text()
        for j, (char, style) in enumerate(parts):
            if j > 0:
                result.append(" ")
            result.append(char, style=style)
        return result

    def __rich__(self) -> Panel:
        outer = Table.grid(padding=(0, 0))
        outer.add_column()

        for dr in self._results:
            tracker = dr.tracker

            # Find active/last phase info
            active_detail = ""
            overall = "pending"
            for i, s in enumerate(tracker.statuses):
                if s == "active":
                    overall = "active"
                    active_detail = tracker.phases[i]
                    d = tracker.details[i]
                    if d:
                        active_detail += f" — {d}"
                    break
                elif s == "fail":
                    overall = "fail"
                    active_detail = tracker.phases[i]
                    d = tracker.details[i]
                    if d:
                        active_detail += f" — {d}"
                    break
            if overall == "pending" and all(
                s in ("ok", "skip") for s in tracker.statuses
            ):
                overall = "done"

            # Device header row with status icon
            row = Table.grid(padding=(0, 1))
            row.add_column(width=3)
            row.add_column(min_width=30)
            row.add_column()

            if overall == "active":
                icon: object = self._spinner
                label = Text.from_markup(
                    f"[bold cyan]{dr.device_label}[/bold cyan]"
                )
            elif overall == "fail":
                icon = Text.from_markup("[red]✗[/red]")
                label = Text.from_markup(
                    f"[red]{dr.device_label}[/red]"
                )
            elif overall == "done":
                icon = Text.from_markup("[green]✓[/green]")
                label = Text.from_markup(f"{dr.device_label}")
            else:
                icon = Text.from_markup("[dim]○[/dim]")
                label = Text.from_markup(f"[dim]{dr.device_label}[/dim]")

            steps = self._step_icons(tracker)
            row.add_row(icon, label, steps)
            outer.add_row(row)

            # Detail line showing current/last phase
            if active_detail:
                detail_style = "red" if overall == "fail" else "dim"
                outer.add_row(
                    Text.from_markup(f"    [{detail_style}]{active_detail}[/{detail_style}]")
                )
            elif overall == "done":
                outer.add_row(Text.from_markup("    [dim]Complete[/dim]"))
            else:
                outer.add_row(Text.from_markup("    [dim]Waiting…[/dim]"))

            # Spacer between devices
            outer.add_row(Text(""))

        return Panel(
            outer,
            title="[bold]Parallel Execution[/bold]",
            border_style="cyan",
            padding=(1, 2),
        )


# --------------------------------------------------------------------------- #
#  Bulk common-settings push
# --------------------------------------------------------------------------- #

# An IPv4 address in dot-decimal notation.
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
# A line that carries a field label, e.g. "DNS Server....... 10.0.0.1".
# Used to tell a labelled line from a bare continuation line.
_LABELLED_LINE_RE = re.compile(r"[A-Za-z]{2,}")


def parse_dns_servers(ipconfig_output: str) -> list[str]:
    """Extract the configured DNS servers from ``IPCONFIG /ALL`` output.

    Written to tolerate several layouts, because the exact wording varies
    between Crestron models and firmware revisions.  Any line whose label
    mentions DNS contributes every IPv4 address on it, and bare
    address-only lines immediately following one are treated as
    continuations (the multi-server layout).

    Returns addresses in the order seen, de-duplicated, with unset
    placeholders (0.0.0.0) dropped.  An unrecognised layout yields an empty
    list rather than a wrong answer.
    """
    found: list[str] = []
    in_dns_block = False

    for raw in ipconfig_output.splitlines():
        line = raw.strip()
        if not line:
            in_dns_block = False
            continue

        addresses = _IPV4_RE.findall(line)
        is_dns_label = "dns" in line.lower()

        if is_dns_label:
            # A DNS label with no address (e.g. "DNS Suffix ... :") still
            # opens the block, so a following bare address is picked up.
            found.extend(addresses)
            in_dns_block = True
            continue

        # A different labelled field ends the DNS block.
        label_part = _IPV4_RE.sub("", line)
        if _LABELLED_LINE_RE.search(label_part):
            in_dns_block = False
            continue

        if in_dns_block:
            found.extend(addresses)

    seen: set[str] = set()
    servers: list[str] = []
    for addr in found:
        if addr in ("0.0.0.0", "255.255.255.255") or addr in seen:
            continue
        # Reject malformed matches like 999.1.1.1
        if any(int(octet) > 255 for octet in addr.split(".")):
            continue
        seen.add(addr)
        servers.append(addr)
    return servers


def plan_dns_changes(
    desired: list[str],
    current: list[str],
    mode: str = "replace",
) -> tuple[list[str], list[str]]:
    """Work out which DNS servers to remove and which to add.

    In "replace" mode the device's list is reconciled against ``desired``;
    in "append" mode nothing is removed.  Servers already present are left
    alone, so applying the same list twice is a no-op.

    Returns ``(to_remove, to_add)``.
    """
    desired_unique = list(dict.fromkeys(d for d in desired if d))
    to_add = [d for d in desired_unique if d not in current]
    if mode == "append":
        return [], to_add
    to_remove = [c for c in current if c not in desired_unique]
    return to_remove, to_add


def build_common_setting_commands(
    settings: CommonSettings,
    current_dns: list[str] | None = None,
    now: datetime | None = None,
) -> list[tuple[str, str]]:
    """Build the CLI commands for a bulk settings push.

    Returns ``(command, human_label)`` pairs in the order they should be
    sent.  ``current_dns`` is what the device reports today, used to compute
    a minimal set of DNS changes; pass None to skip reconciliation and only
    add.  Only fields set on ``settings`` produce commands, so an empty
    bundle produces an empty list.
    """
    cmds: list[tuple[str, str]] = []

    if settings.timezone is not None:
        cmds.append((f"TIMEZONE {settings.timezone}",
                     f"Timezone → {settings.timezone}"))

    if settings.sync_time:
        stamp = now or datetime.now()
        cmds.append((
            f"TIMEDATE {stamp.strftime('%H:%M:%S')} {stamp.strftime('%m-%d-%Y')}",
            "Set date/time",
        ))

    if settings.ntp_server is not None:
        cmds.append((f"SNTP SERVER:{settings.ntp_server}",
                     f"NTP → {settings.ntp_server}"))

    # One SYNC covers both a new server and an explicit time sync.
    if settings.ntp_server is not None or settings.sync_time:
        cmds.append(("SNTP SYNC", "Sync time"))

    if settings.dns_servers is not None:
        to_remove, to_add = plan_dns_changes(
            settings.dns_servers, current_dns or [], settings.dns_mode,
        )
        for dns in to_remove:
            cmds.append((f"REMDNS {dns}", f"Remove DNS {dns}"))
        for dns in to_add:
            cmds.append((f"ADDDNS {dns}", f"Add DNS {dns}"))

    if settings.web_port is not None:
        cmds.append((f"WEBPORT {settings.web_port}",
                     f"Web port → {settings.web_port}"))
    if settings.secure_web_port is not None:
        cmds.append((f"SECUREWEBPORT {settings.secure_web_port}",
                     f"Secure web port → {settings.secure_web_port}"))
    if settings.user_login_attempts is not None:
        cmds.append((f"SETUSERLOGINATTEMPTS {settings.user_login_attempts}",
                     f"User login attempts → {settings.user_login_attempts}"))
    if settings.user_lockout_time is not None:
        cmds.append((f"SETUSERLOCKOUTTIME {settings.user_lockout_time}",
                     f"User lockout time → {settings.user_lockout_time}"))
    if settings.login_attempts is not None:
        cmds.append((f"SETLOGINATTEMPTS {settings.login_attempts}",
                     f"Console login attempts → {settings.login_attempts}"))
    if settings.lockout_time is not None:
        cmds.append((f"SETLOCKOUTTIME {settings.lockout_time}",
                     f"Console lockout time → {settings.lockout_time}"))
    if settings.fips_mode is not None:
        cmds.append((f"FIPSMODE {settings.fips_mode}",
                     f"FIPS mode → {settings.fips_mode}"))

    return cmds


@dataclass
class SettingsPushResult:
    """Outcome of pushing common settings to one device."""

    host: str
    success: bool
    detail: str = ""
    commands: list[str] = field(default_factory=list)
    current_dns: list[str] = field(default_factory=list)


def apply_common_settings(
    device: Device,
    username: str,
    password: str,
    settings: CommonSettings,
    config: Config,
    dry_run: bool = False,
) -> SettingsPushResult:
    """Push the settings in ``settings`` to one device.

    Opens a single SSH session, reads the current DNS list when DNS is being
    reconciled, then sends only the commands the bundle calls for.  Never
    touches IP address, mask, gateway or hostname, and never reboots.

    Safe to call concurrently for different devices.
    """
    host = device.ip or device.hostname
    if settings.is_empty:
        return SettingsPushResult(host, True, "Nothing to apply")

    needs_current_dns = (
        settings.dns_servers is not None and settings.dns_mode == "replace"
    )

    try:
        with CrestronSSH(host, username, password,
                         use_key_auth=config.ssh_key_auth) as ssh:
            if not device.model and ssh.model:
                device.model = ssh.model

            current_dns: list[str] = []
            if needs_current_dns:
                ipconfig = ssh.send_command("IPCONFIG /ALL", timeout=15)
                current_dns = parse_dns_servers(ipconfig)

            cmds = build_common_setting_commands(settings, current_dns)
            if not cmds:
                return SettingsPushResult(
                    host, True, "Already up to date", [], current_dns,
                )

            if dry_run:
                return SettingsPushResult(
                    host, True, f"Would send {len(cmds)} command(s)",
                    [c for c, _ in cmds], current_dns,
                )

            for cmd, _label in cmds:
                ssh.send_command(cmd, timeout=20)

            detail = f"{len(cmds)} command(s) applied"
            if settings.needs_reboot:
                detail += " (reboot needed for FIPS)"
            return SettingsPushResult(
                host, True, detail, [c for c, _ in cmds], current_dns,
            )
    except Exception as e:
        return SettingsPushResult(host, False, str(e)[:70])
