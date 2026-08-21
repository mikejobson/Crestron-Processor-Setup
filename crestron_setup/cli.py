"""Interactive CLI console for Crestron processor provisioning."""

from __future__ import annotations

import glob as _glob_module
import os
import select
import sys
import time
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path as _Path
from dataclasses import dataclass
from typing import TYPE_CHECKING

try:
    import termios
    import tty
    _HAS_TERMIOS = True
except ImportError:
    _HAS_TERMIOS = False

import questionary
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from .config import load_config, save_config
from .discovery import discover_devices, print_device_table
from .firmware import cache_info, clear_cache, download_firmware, download_firmware_quiet, find_local_firmware
from .models import CommonSettings, Config, Device, NetworkConfig, Profile, SKIP, resolve_profile
from .provisioning import (
    DeviceResult,
    _ParallelDisplay,
    _StepTracker,
    _show_dry_run_results,
    provision_device,
    restore_device,
    upload_program,
)
from .ssh import CrestronFirstBoot

if TYPE_CHECKING:
    # Imported for annotations only — the runtime imports happen inside the
    # flows that need a connection, to keep startup light.
    from .ctp import CrestronCTP
    from .ssh import CrestronSSH

    # Console connections: CrestronSSH and CrestronCTP share the same
    # send_command() / disconnect() API.
    _ConsoleConn = CrestronSSH | CrestronCTP
from .timezones import timezone_choices, timezone_label
from .updater import (
    InstallMethod,
    can_self_update,
    check_for_update,
    detect_install_method,
    self_update,
    update_instructions,
)
from . import __version__

console = Console()

# Populated by background update check at startup
_update_info: tuple[str, str] | None = None
_install_method: InstallMethod = InstallMethod.DEV


def _clear() -> None:
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def match_profile(model: str, config: Config) -> str | None:
    """Find the first profile whose model patterns match a device model."""
    if not model or not config.profiles:
        return None
    for name, profile in config.profiles.items():
        if profile.matches_model(model):
            return name
    return None


def _prompt_profile_selection(
    config: Config,
    suggested: str | None = None,
    show_auto_match: bool = False,
) -> str | None:
    """Prompt the user to select a configuration profile.

    Returns profile name, None for default (no profile), or "__auto__"
    for auto-match by model.
    """
    if not config.profiles:
        return None

    choices = []
    if show_auto_match:
        choices.append(questionary.Choice(
            "Auto-match by model (Recommended)",
            value="__auto__",
        ))
    if suggested:
        choices.append(questionary.Choice(
            f"{suggested} (suggested)",
            value=suggested,
        ))
    choices.append(questionary.Choice("Default (no profile)", value=None))
    for name in config.profiles:
        if name != suggested:
            choices.append(questionary.Choice(name, value=name))

    return questionary.select(
        "Configuration profile:",
        choices=choices,
    ).ask()


def _load_animation() -> tuple[list, int]:
    """Load and parse the welcome animation JSON into frame data.

    Returns (frames, canvas_height) where frames is a list of
    (line_text, color_map) tuples, color_map is {(col, row): hex_color}.
    """
    import json
    from pathlib import Path

    try:
        # PyInstaller extracts data files to sys._MEIPASS
        base = Path(getattr(sys, "_MEIPASS", ""))
        anim_file = base / "crestron_setup" / "welcome_animation.json"
        if not anim_file.is_file():
            from importlib.resources import files

            anim_file = files("crestron_setup").joinpath("welcome_animation.json")
        data = json.loads(anim_file.read_text(encoding="utf-8"))
    except Exception:
        return [], 0

    canvas_height = data.get("canvas", {}).get("height", 22)
    frames = []
    for frame in data["frames"]:
        lines = frame["contentString"].split("\n")

        # Parse foreground color map
        fg_raw = frame.get("colors", {}).get("foreground", "{}")
        if isinstance(fg_raw, str):
            fg_map = json.loads(fg_raw)
        else:
            fg_map = fg_raw

        # Convert "x,y" keys to (x, y) tuples
        color_map: dict[tuple[int, int], str] = {}
        for key, color in fg_map.items():
            parts = key.split(",")
            color_map[(int(parts[0]), int(parts[1]))] = color

        frames.append((lines, color_map))

    return frames, canvas_height


def _render_frame(
    lines: list[str],
    color_map: dict[tuple[int, int], str],
    target_height: int = 0,
) -> Text:
    """Render a single animation frame as a Rich Text object with per-char colors."""
    result = Text()
    # Pad to target height so text below doesn't jump
    padded = list(lines)
    while target_height and len(padded) < target_height:
        padded.append("")
    for row, line in enumerate(padded):
        for col, char in enumerate(line):
            color = color_map.get((col, row))
            if color:
                result.append(char, style=color)
            else:
                result.append(char)
        if row < len(padded) - 1:
            result.append("\n")
    return result


def _key_pressed() -> bool:
    """Check if a key has been pressed (non-blocking)."""
    if not _HAS_TERMIOS:
        # Windows: use msvcrt if available
        try:
            import msvcrt
            return msvcrt.kbhit()
        except ImportError:
            return False
    try:
        return bool(select.select([sys.stdin], [], [], 0)[0])
    except Exception:
        return False


def _splash() -> None:
    """Show the animated welcome screen looping until any key is pressed."""
    _clear()

    frames, canvas_height = _load_animation()
    if not frames:
        # Fallback: simple text banner if animation file missing
        console.print(
            Panel(
                Text.assemble(
                    Text("Crestron Processor Setup", style="bold cyan"),
                    "  ",
                    Text(f"v{__version__}", style="dim"),
                ),
                border_style="cyan",
                padding=(0, 2),
            )
        )
        console.print()
        questionary.press_any_key_to_continue("Press any key to continue...").ask()
        return

    # Build the static info text shown below the animation
    info = Text.from_markup(
        f"\n[bold cyan]Crestron Processor Setup[/bold cyan]  [dim]v{__version__}[/dim]\n"
        "\n"
        "[dim]Automated provisioning tool for Crestron control processors.\n"
        "Configure settings in ~/.config/crestron-setup/config.yaml\n"
        "or create a config.yaml file in this directory.\n"
        "\n"
        "Press any key to continue…[/dim]"
    )

    # Switch terminal to cbreak mode so keypresses are immediate
    old_settings = None
    if _HAS_TERMIOS:
        fd = sys.stdin.fileno()
        try:
            old_settings = termios.tcgetattr(fd)
            tty.setcbreak(fd)
        except Exception:
            pass

    try:
        with Live(console=console, refresh_per_second=30, transient=True) as live:
            while True:
                for lines, color_map in frames:
                    if _key_pressed():
                        # Drain the keypress
                        try:
                            sys.stdin.read(1)
                        except Exception:
                            pass
                        return
                    rendered = _render_frame(lines, color_map, canvas_height)
                    rendered.append_text(info)
                    live.update(rendered)
                    time.sleep(1 / 30)
    finally:
        if old_settings is not None:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _banner() -> None:
    """Print the application banner at the top of the screen."""
    title = Text("Crestron Processor Setup", style="bold cyan")
    subtitle = Text(f"v{__version__}", style="dim")
    console.print(
        Panel(
            Text.assemble(title, "  ", subtitle),
            border_style="cyan",
            padding=(0, 2),
        )
    )
    if _update_info:
        latest, _ = _update_info
        console.print(
            f"  [yellow]Update available:[/yellow] v{latest}  "
            f"[dim]({update_instructions(_install_method)})[/dim]"
        )
    console.print()


def _header(section: str) -> None:
    """Clear screen and show banner + section header."""
    _clear()
    _banner()
    console.rule(f"[bold]{section}[/bold]")
    console.print()


def _pause() -> None:
    """Wait for user to press Enter before returning to menu."""
    console.print()
    questionary.press_any_key_to_continue("Press any key to continue...").ask()


def main() -> None:
    """Entry point for the Crestron setup console."""
    global _update_info, _install_method
    config = load_config()

    # Start update check in background so it doesn't slow startup
    _install_method = detect_install_method()
    update_future: Future = ThreadPoolExecutor(1).submit(check_for_update)

    _splash()

    # Collect result after splash (should be done by now)
    if _update_info is None:
        try:
            _update_info = update_future.result(timeout=2)
        except Exception:
            pass

    while True:
        _clear()
        _banner()

        menu_choices = [
            questionary.Choice("Discover Devices", value="discover"),
            questionary.Choice("Setup Device (manual IP)", value="setup"),
            questionary.Choice("Batch Provision (CSV/YAML)", value="batch"),
            questionary.Choice("Upload Program", value="program"),
            questionary.Choice("Deploy Project (UC Engine)", value="project"),
            questionary.Choice("Firmware Audit", value="fw_audit"),
            questionary.Choice("Certificate Management", value="certs"),
            questionary.Choice("IP Table Management", value="iptable"),
            questionary.Choice("Account Management", value="accounts"),
            questionary.Choice("Restore & Erase Device", value="restore"),
            questionary.Choice("Download Firmware", value="firmware"),
            questionary.Choice("Clear Firmware Cache", value="cache"),
            questionary.Choice("Settings", value="settings"),
        ]
        if _update_info and can_self_update(_install_method):
            latest, _ = _update_info
            menu_choices.append(
                questionary.Choice(f"Update Now (v{latest})", value="update")
            )
        menu_choices.append(questionary.Choice("Exit", value="exit"))

        choice = questionary.select("Main Menu", choices=menu_choices).ask()

        if choice is None or choice == "exit":
            _clear()
            console.print("[dim]Goodbye.[/dim]")
            break
        elif choice == "discover":
            config = _flow_discover(config)
        elif choice == "setup":
            _flow_manual_setup(config)
        elif choice == "batch":
            config = _flow_batch_provision(config)
        elif choice == "program":
            config = _flow_upload_program(config)
        elif choice == "project":
            config = _flow_deploy_project(config)
        elif choice == "restore":
            _flow_restore(config)
        elif choice == "fw_audit":
            _flow_firmware_audit(config)
        elif choice == "certs":
            config = _flow_cert_management(config)
        elif choice == "iptable":
            config = _flow_ip_table(config)
        elif choice == "accounts":
            config = _flow_account_mgmt(config)
        elif choice == "firmware":
            _flow_firmware(config)
        elif choice == "cache":
            _flow_clear_cache()
        elif choice == "settings":
            config = _flow_settings(config)
        elif choice == "update":
            _flow_update()


# --------------------------------------------------------------------------- #
#  Discovery flow
# --------------------------------------------------------------------------- #


def _first_boot_panel(spinner: Spinner, done: int, total: int,
                      first_boot: list[str]) -> Panel:
    """Build a live panel showing first-boot check progress."""
    grid = Table.grid(padding=(0, 1))
    grid.add_column(width=3)
    grid.add_column()
    grid.add_row(spinner, Text.from_markup(
        f"[bold cyan]Checking first-boot state…[/bold cyan] "
        f"[dim]{done}/{total} devices[/dim]"))
    if first_boot:
        grid.add_row("", Text.from_markup(
            f"[yellow]{len(first_boot)} in first-boot mode[/yellow]"))
        for host in first_boot[-8:]:
            grid.add_row("", Text.from_markup(f"  [yellow]•[/yellow] {host}"))
    return Panel(grid, title="[bold]First-Boot Check[/bold]",
                 border_style="cyan", padding=(1, 2))


def _check_first_boot_states(devices: list[Device], config: Config) -> None:
    """Populate ``is_first_boot`` on every device, checking them in parallel.

    Devices are probed concurrently with a per-device time budget, so a large
    or partly-unreachable estate no longer costs the sum of every timeout.
    """
    if not devices:
        return

    by_host: dict[str, list[Device]] = {}
    for dev in devices:
        host = dev.ip or dev.hostname
        if host:
            by_host.setdefault(host, []).append(dev)
        else:
            dev.is_first_boot = False

    if not by_host:
        return

    # Count only devices we can actually reach, so the counter ends at N/N
    total = sum(len(v) for v in by_host.values())

    spinner = Spinner("dots", style="cyan")
    progress = {"done": 0}
    first_boot: list[str] = []

    with Live(_first_boot_panel(spinner, 0, total, first_boot),
              console=console, refresh_per_second=10) as live:

        def _on_result(host: str, is_first_boot: bool) -> None:
            for dev in by_host.get(host, ()):
                dev.is_first_boot = is_first_boot
            progress["done"] += len(by_host.get(host, ()))
            if is_first_boot:
                first_boot.append(host)
            live.update(_first_boot_panel(spinner, progress["done"], total,
                                          first_boot))

        CrestronFirstBoot.check_first_boot_batch(
            list(by_host),
            budget=config.discovery_probe_timeout,
            max_workers=config.discovery_probe_workers,
            on_result=_on_result,
        )


def _flow_discover(config: Config) -> Config:
    """Discover devices on the LAN, select an action, pick devices, and execute."""
    _header("Discover Devices")
    devices = discover_devices(config, console)

    if not devices:
        console.print("[yellow]No devices found.[/yellow] "
                      "Make sure you're on the same subnet and running with "
                      "elevated privileges (sudo).")
        _pause()
        return config

    # Check first-boot state for all devices (in parallel)
    _check_first_boot_states(devices, config)

    _header("Discover Devices")
    print_device_table(devices, console)
    console.print()

    # Pick action first
    action = questionary.select(
        "What do you want to do?",
        choices=[
            questionary.Choice("Provision", value="provision"),
            questionary.Choice("Provision (Dry Run)", value="dry_run"),
            questionary.Choice("Apply Common Settings (DNS/NTP/timezone…)",
                               value="apply_settings"),
            questionary.Choice("Deploy Certificate", value="deploy_cert"),
            questionary.Choice("IP Table", value="iptable"),
            questionary.Choice("Account Management", value="accounts"),
            questionary.Choice("Upload Program", value="program"),
            questionary.Choice("Deploy Project (UC Engine)", value="project"),
            questionary.Choice("Restore & Erase", value="restore"),
            questionary.Choice("Back to Main Menu", value="back"),
        ],
    ).ask()

    if action is None or action == "back":
        return config

    # Select devices — single select for IP table, multi-select for others
    device_choices = [
        questionary.Choice(
            f"{dev.ip:<17} {dev.hostname:<20} {dev.model:<12} "
            f"{'[FIRST BOOT]' if dev.is_first_boot else ''}",
            value=i,
        )
        for i, dev in enumerate(devices)
    ]

    if action in ("iptable", "accounts"):
        selected_idx = questionary.select(
            "Select device:",
            choices=device_choices,
        ).ask()
        if selected_idx is None:
            return config
        selected_indices = [selected_idx]
    else:
        selected_indices = questionary.checkbox(
            "Select devices:",
            choices=device_choices,
        ).ask()

    if not selected_indices:
        console.print("[dim]No devices selected.[/dim]")
        _pause()
        return config

    selected_devices = [devices[i] for i in selected_indices]

    # Get credentials (all actions need them)
    creds = _prompt_credentials(config)
    if not creds:
        return config
    username, password = creds

    # Gather action-specific inputs before starting parallel execution
    program_path: str = ""
    project_path: str = ""
    slot: int = 1

    if action in ("provision", "dry_run"):
        # Network configuration per device
        if len(selected_devices) == 1:
            net = _prompt_network_config(selected_devices[0].ip)
            if net:
                selected_devices[0].network = net
        else:
            net_mode = questionary.select(
                "Network configuration:",
                choices=[
                    questionary.Choice("Skip (keep DHCP on all)", value="skip"),
                    questionary.Choice("Configure each device individually", value="each"),
                ],
            ).ask()
            if net_mode == "each":
                for dev in selected_devices:
                    net = _prompt_network_config(dev.ip)
                    if net:
                        dev.network = net

        # Check firmware availability for unique models
        models_with_url: set[str] = set()
        for dev in selected_devices:
            if dev.model and config.firmware_urls.get(dev.model.upper()):
                models_with_url.add(dev.model.upper())

        if models_with_url:
            # Show current local firmware status per model
            for mdl in sorted(models_with_url):
                fw_path, fw_ver = find_local_firmware(mdl, config)
                if fw_path:
                    console.print(
                        f"[cyan][INFO][/cyan] {mdl}: local firmware {fw_path.name} (v{fw_ver})"
                    )
                else:
                    console.print(
                        f"[cyan][INFO][/cyan] {mdl}: no local firmware found"
                    )

            dl = questionary.confirm(
                "Check for latest firmware from download URL?", default=True,
            ).ask()
            if dl:
                for mdl in sorted(models_with_url):
                    console.print()
                    download_firmware(mdl, config, console)
                console.print()

    elif action == "program":
        default_path = config.last_program_file or ""
        program_path = questionary.path(
            "Program file path:",
            default=default_path,
        ).ask()
        if not program_path:
            return config

        slot_input = questionary.text("Program slot:", default="1").ask()
        if not slot_input:
            return config
        try:
            slot = int(slot_input)
            if slot < 1:
                raise ValueError
        except ValueError:
            console.print("[red]Invalid slot number.[/red]")
            _pause()
            return config

        config.last_program_file = program_path
        save_config(config)

    elif action == "project":
        default_path = config.last_project_file or ""
        project_path = questionary.path(
            "CH5Z project file path:",
            default=default_path,
        ).ask()
        if not project_path:
            return config

        if not _Path(project_path).expanduser().exists():
            console.print("[red]File not found.[/red]")
            _pause()
            return config

        config.last_project_file = project_path
        save_config(config)

    elif action == "restore":
        device_list = ", ".join(d.ip or d.hostname for d in selected_devices)
        console.print(f"\n[yellow][WARN][/yellow] This will erase all settings and "
                      f"programs on: {device_list}\n")
        confirm = questionary.confirm(
            "Are you sure you want to erase and restore these devices?",
            default=False,
        ).ask()
        if not confirm:
            console.print("[dim]Cancelled.[/dim]")
            _pause()
            return config

    # ── Bulk settings push: handled separately ──────────────────────────
    if action == "apply_settings":
        config = _flow_bulk_apply_settings(
            selected_devices, username, password, config,
        )
        _pause()
        return config

    # ── Deploy certificate: handled separately ──────────────────────────
    if action == "deploy_cert":
        _flow_bulk_deploy_cert(selected_devices, username, password, config)
        _pause()
        return config

    # Profile selection for provision actions
    profile_name: str | None = None
    device_profiles: dict[int, str | None] | None = None
    if action in ("provision", "dry_run") and config.profiles:
        # Auto-suggest based on device models
        models = {d.model for d in selected_devices if d.model}
        suggested = None
        for m in models:
            suggested = match_profile(m, config)
            if suggested:
                break
        has_multiple = len(selected_devices) > 1
        profile_name = _prompt_profile_selection(
            config, suggested, show_auto_match=has_multiple,
        )

        if profile_name == "__auto__":
            # Build per-device profile mapping and show preview
            device_profiles = {}
            for i, dev in enumerate(selected_devices):
                device_profiles[i] = match_profile(dev.model, config) if dev.model else None

            # Show preview table
            table = Table(
                title="Profile Auto-Match Preview",
                border_style="cyan",
                show_lines=False,
            )
            table.add_column("Device", style="cyan", min_width=18)
            table.add_column("Model", min_width=12)
            table.add_column("Profile", min_width=15)

            for i, dev in enumerate(selected_devices):
                host = dev.ip or dev.hostname
                prof = device_profiles[i] or "[dim]default[/dim]"
                table.add_row(host, dev.model or "—", prof)

            console.print(table)
            console.print()

            confirm = questionary.confirm("Proceed with these profile assignments?").ask()
            if not confirm:
                return config

            profile_name = None  # Clear — we use device_profiles instead

    # ── Single device: run normally with full display ──────────────────
    if len(selected_devices) == 1:
        dev = selected_devices[0]
        effective_profile = (
            device_profiles[0] if device_profiles else profile_name
        )
        if action == "provision":
            provision_device(dev, username, password, config, console,
                             profile_name=effective_profile)
        elif action == "dry_run":
            provision_device(dev, username, password, config, console,
                             dry_run=True, profile_name=effective_profile)
        elif action == "program":
            host = dev.ip or dev.hostname
            upload_program(host, username, password, program_path, slot, console, use_key_auth=config.ssh_key_auth)
        elif action == "project":
            host = dev.ip or dev.hostname
            _deploy_project_single(host, username, password, project_path, console)
        elif action == "restore":
            restore_device(dev, username, password, console, use_key_auth=config.ssh_key_auth)
        elif action == "iptable":
            _flow_ip_table(config, host=dev.ip or dev.hostname,
                           username=username, password=password,
                           model=dev.model)
            return config
        elif action == "accounts":
            _flow_account_mgmt(config, host=dev.ip or dev.hostname,
                               username=username, password=password)
            return config
        _pause()
        return config

    # ── Multiple devices: run in parallel with combined display ────────
    device_results = _run_parallel(
        action, selected_devices, username, password,
        config, program_path, slot, profile_name=profile_name,
        device_profiles=device_profiles, project_path=project_path,
    )
    _show_parallel_summary(device_results, config)
    return config


# --------------------------------------------------------------------------- #
#  Parallel execution helpers
# --------------------------------------------------------------------------- #


def _run_parallel(
    action: str,
    devices: list[Device],
    username: str,
    password: str,
    config: Config,
    program_path: str = "",
    slot: int = 1,
    profile_name: str | None = None,
    device_profiles: dict[int, str | None] | None = None,
    project_path: str = "",
) -> list[DeviceResult]:
    """Run an action on multiple devices in parallel with a combined live display."""
    # Pre-create DeviceResult entries with placeholder trackers for display
    device_results: list[DeviceResult] = []
    for dev in devices:
        ip = dev.ip or dev.hostname
        label = f"{ip}  {dev.hostname}" if dev.hostname and dev.hostname != ip else ip
        if dev.model:
            label += f"  ({dev.model})"
        if action == "provision":
            from .provisioning import PHASE_NAMES
            tracker = _StepTracker(label, list(PHASE_NAMES))
        elif action == "dry_run":
            from .provisioning import PHASE_NAMES
            tracker = _StepTracker(label, list(PHASE_NAMES))
            tracker._panel_title = f"Provision (Dry Run) — {label}"
        elif action == "program":
            from .provisioning import PROGRAM_PHASE_NAMES
            tracker = _StepTracker(label, list(PROGRAM_PHASE_NAMES))
        elif action == "project":
            tracker = _StepTracker(label, ["Upload", "Deploy"])
        else:  # restore
            from .provisioning import RESTORE_PHASE_NAMES
            tracker = _StepTracker(label, list(RESTORE_PHASE_NAMES))
        device_results.append(DeviceResult(
            device_label=label, action=action, success=False, tracker=tracker,
        ))

    display = _ParallelDisplay(device_results)

    def _worker(idx: int, dev: Device, dr: DeviceResult) -> None:
        """Thread worker — runs action headlessly using dr.tracker for live updates."""
        host = dev.ip or dev.hostname
        # Use per-device profile if available, else shared profile
        effective_profile = (
            device_profiles[idx] if device_profiles and idx in device_profiles
            else profile_name
        )
        if action == "provision":
            result = provision_device(
                dev, username, password, config, console,
                headless=True, tracker=dr.tracker,
                profile_name=effective_profile,
            )
            dr.success, _, dr.results = result  # type: ignore[misc]
        elif action == "dry_run":
            result = provision_device(
                dev, username, password, config, console,
                headless=True, tracker=dr.tracker, dry_run=True,
                profile_name=effective_profile,
            )
            dr.success, _, dr.results = result  # type: ignore[misc]
        elif action == "program":
            result = upload_program(
                host, username, password, program_path, slot, console,
                headless=True, tracker=dr.tracker,
                use_key_auth=config.ssh_key_auth,
            )
            dr.success = result[0]  # type: ignore[index]
        elif action == "project":
            dr.success = _deploy_project_worker(
                host, username, password, project_path, dr.tracker,
            )
        elif action == "restore":
            result = restore_device(
                dev, username, password, console,
                headless=True, tracker=dr.tracker,
                use_key_auth=config.ssh_key_auth,
            )
            dr.success = result[0]  # type: ignore[index]

    _clear()
    with Live(display, console=console, refresh_per_second=8) as live:
        with ThreadPoolExecutor(max_workers=len(devices)) as pool:
            futures = [
                pool.submit(_worker, i, dev, dr)
                for i, (dev, dr) in enumerate(zip(devices, device_results))
            ]
            # Poll until all futures complete, refreshing display continuously
            while not all(f.done() for f in futures):
                live.update(display)
                time.sleep(0.25)
        live.update(display)

    return device_results


def _show_parallel_summary(
    device_results: list[DeviceResult],
    config: Config,
) -> None:
    """Show a summary table and let the user drill into individual results."""
    while True:
        _clear()
        _banner()

        # Summary table
        all_ok = all(dr.success for dr in device_results)
        title = ("[bold green]All Devices Complete[/bold green]" if all_ok
                 else "[bold yellow]Results Summary[/bold yellow]")
        border = "green" if all_ok else "yellow"

        table = Table(show_header=True, padding=(0, 1))
        table.add_column("#", style="dim", width=3)
        table.add_column("Device", style="cyan", min_width=18)
        table.add_column("Action", min_width=12)
        table.add_column("Result", min_width=10)
        table.add_column("Details", min_width=30)

        for i, dr in enumerate(device_results):
            status = "[green]✓ OK[/green]" if dr.success else "[red]✗ Failed[/red]"
            # Get last phase detail
            detail = ""
            for j in range(len(dr.tracker.statuses) - 1, -1, -1):
                s = dr.tracker.statuses[j]
                if s in ("ok", "fail", "skip"):
                    detail = dr.tracker.details[j] or dr.tracker.phases[j]
                    if s == "fail":
                        detail = f"[red]{detail}[/red]"
                    break
            action_label = "Provision (Dry Run)" if dr.action == "dry_run" else dr.action.title()
            table.add_row(str(i + 1), dr.device_label, action_label, status, detail)

        console.print(Panel(table, title=title, border_style=border, padding=(1, 2)))
        console.print()

        # Drill-down menu
        choices = [
            questionary.Choice(
                f"{dr.device_label} — {'OK' if dr.success else 'FAILED'}",
                value=i,
            )
            for i, dr in enumerate(device_results)
        ]
        choices.append(questionary.Choice("Back to Main Menu", value=-1))

        pick = questionary.select(
            "View details for a device:",
            choices=choices,
        ).ask()

        if pick is None or pick == -1:
            return

        # Show detailed tracker for selected device
        dr = device_results[pick]
        _clear()
        _banner()

        if dr.action == "dry_run" and dr.results:
            # Reconstruct resolved profile for skipped-field display
            dr_profile = dr.results.get("profile")
            dr_resolved = resolve_profile(dr_profile, config) if dr_profile else None
            effective_config = dr_resolved.config if dr_resolved else config
            _show_dry_run_results(
                console, dr.tracker, dr.results, dr.success, effective_config,
                resolved=dr_resolved,
            )
        else:
            success_label = "[bold green]Success[/bold green]" if dr.success else "[bold red]Failed[/bold red]"
            console.print(
                Panel(
                    dr.tracker.render_static(),
                    title=f"{dr.device_label} — {success_label}",
                    border_style="green" if dr.success else "red",
                    padding=(1, 2),
                )
            )
            console.print()
        _pause()


# --------------------------------------------------------------------------- #
#  Manual setup flow
# --------------------------------------------------------------------------- #


def _flow_manual_setup(config: Config) -> None:
    """Provision a single device by IP/hostname."""
    _header("Setup Device")
    host = questionary.text("Processor hostname or IP:").ask()
    if not host:
        return

    creds = _prompt_credentials(config)
    if not creds:
        return
    username, password = creds

    device = Device(ip=host)

    # Quick first-boot check
    with console.status("Checking first-boot state…", spinner="dots"):
        device.is_first_boot = CrestronFirstBoot.check_first_boot(
            host, budget=config.discovery_probe_timeout)
    if device.is_first_boot:
        console.print("[cyan][INFO][/cyan] Device appears to be in first-boot mode.")

    # Network configuration
    net = _prompt_network_config(host)
    if net:
        device.network = net

    mode = questionary.select(
        "Run mode:",
        choices=[
            questionary.Choice("Provision (apply changes)", value="provision"),
            questionary.Choice("Provision (Dry Run)", value="dry_run"),
        ],
    ).ask()
    if not mode:
        return

    # Profile selection
    profile_name: str | None = None
    if config.profiles:
        profile_name = _prompt_profile_selection(config)

    provision_device(
        device, username, password, config, console,
        dry_run=(mode == "dry_run"),
        profile_name=profile_name,
    )
    _pause()


# --------------------------------------------------------------------------- #
#  Batch Provision flow
# --------------------------------------------------------------------------- #


def _flow_batch_provision(config: Config) -> Config:
    """Provision multiple devices from a CSV or YAML batch file."""
    import csv
    from pathlib import Path

    import yaml

    _header("Batch Provision")

    # Pick the batch file
    file_path = questionary.path(
        "Path to batch file (CSV or YAML):",
        only_directories=False,
    ).ask()
    if not file_path:
        return config

    path = Path(file_path).expanduser().resolve()
    if not path.is_file():
        console.print(f"[red][FAIL][/red] File not found: {path}")
        _pause()
        return config

    # Parse the batch file
    entries: list[dict[str, str]] = []
    ext = path.suffix.lower()

    try:
        if ext in (".yaml", ".yml"):
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict) or "devices" not in data:
                console.print("[red][FAIL][/red] YAML must have a top-level 'devices' list.")
                _pause()
                return config
            raw_list = data["devices"]
            if not isinstance(raw_list, list):
                console.print("[red][FAIL][/red] 'devices' must be a list.")
                _pause()
                return config
            for item in raw_list:
                if isinstance(item, str):
                    entries.append({"hostname": item})
                elif isinstance(item, dict):
                    entries.append({k: str(v) for k, v in item.items()})
        elif ext == ".csv":
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    entries.append({k.strip().lower(): (v or "").strip() for k, v in row.items()})
        else:
            console.print(f"[red][FAIL][/red] Unsupported file type: {ext}")
            console.print("[dim]Supported: .csv, .yaml, .yml[/dim]")
            _pause()
            return config
    except Exception as e:
        console.print(f"[red][FAIL][/red] Error reading batch file: {e}")
        _pause()
        return config

    if not entries:
        console.print("[yellow][WARN][/yellow] No devices found in batch file.")
        _pause()
        return config

    # Validate entries — hostname is required
    valid_entries: list[dict[str, str]] = []
    for i, entry in enumerate(entries, 1):
        host = entry.get("hostname") or entry.get("ip") or entry.get("host") or ""
        if not host:
            console.print(f"[yellow][WARN][/yellow] Row {i}: Missing hostname/ip — skipped.")
            continue
        entry["_host"] = host
        valid_entries.append(entry)

    if not valid_entries:
        console.print("[red][FAIL][/red] No valid devices in batch file.")
        _pause()
        return config

    # Show what we found
    table = Table(title="Batch Devices", border_style="cyan", show_lines=False)
    table.add_column("#", style="dim", width=3)
    table.add_column("Hostname / IP", style="cyan", min_width=20)
    table.add_column("Username", min_width=12)
    table.add_column("Profile", min_width=12)

    has_per_device_creds = any(entry.get("username") for entry in valid_entries)

    for i, entry in enumerate(valid_entries, 1):
        table.add_row(
            str(i),
            entry["_host"],
            entry.get("username", "") or "[dim]—[/dim]",
            entry.get("profile", "") or "[dim]—[/dim]",
        )
    console.print(table)
    console.print(f"\n[cyan]{len(valid_entries)}[/cyan] device(s) loaded from {path.name}\n")

    # Prompt for shared credentials (used where per-device creds not specified)
    if has_per_device_creds:
        console.print("[dim]Some devices have credentials in the batch file.[/dim]")
        need_shared = any(not entry.get("username") for entry in valid_entries)
        if need_shared:
            console.print("[dim]Devices without credentials will use shared credentials.[/dim]")
            creds = _prompt_credentials(config)
            if not creds:
                return config
            shared_user, shared_pass = creds
        else:
            shared_user, shared_pass = "", ""
    else:
        console.print("[dim]Enter credentials to use for all devices.[/dim]")
        creds = _prompt_credentials(config)
        if not creds:
            return config
        shared_user, shared_pass = creds

    # Run mode
    mode = questionary.select(
        "Run mode:",
        choices=[
            questionary.Choice("Provision (apply changes)", value="provision"),
            questionary.Choice("Provision (Dry Run)", value="dry_run"),
        ],
    ).ask()
    if not mode:
        return config

    # Profile selection — use per-device profile if specified, else prompt for shared
    shared_profile: str | None = None
    has_per_device_profile = any(entry.get("profile") for entry in valid_entries)
    need_shared_profile = any(not entry.get("profile") for entry in valid_entries)

    if config.profiles and need_shared_profile:
        if has_per_device_profile:
            console.print("[dim]Devices without a profile will use the shared selection.[/dim]")
        shared_profile = _prompt_profile_selection(config)

    # Build Device objects and run
    devices: list[Device] = []
    device_creds: list[tuple[str, str]] = []
    device_profiles: list[str | None] = []

    for entry in valid_entries:
        dev = Device(ip=entry["_host"])
        devices.append(dev)

        user = entry.get("username") or shared_user
        pw = entry.get("password") or shared_pass
        device_creds.append((user, pw))

        prof = entry.get("profile") or shared_profile
        device_profiles.append(prof if prof else None)

    action = "dry_run" if mode == "dry_run" else "provision"

    # Run in parallel using existing infrastructure
    device_results = _run_parallel_batch(
        action, devices, device_creds, device_profiles, config,
    )
    _show_parallel_summary(device_results, config)
    return config


def _run_parallel_batch(
    action: str,
    devices: list[Device],
    device_creds: list[tuple[str, str]],
    device_profiles: list[str | None],
    config: Config,
) -> list[DeviceResult]:
    """Run provision/dry-run on multiple devices with per-device creds and profiles."""
    from .provisioning import PHASE_NAMES

    device_results: list[DeviceResult] = []
    for dev in devices:
        ip = dev.ip or dev.hostname
        label = ip
        tracker = _StepTracker(label, list(PHASE_NAMES))
        if action == "dry_run":
            tracker._panel_title = f"Provision (Dry Run) — {label}"
        device_results.append(DeviceResult(
            device_label=label, action=action, success=False, tracker=tracker,
        ))

    display = _ParallelDisplay(device_results)

    def _worker(idx: int) -> None:
        dev = devices[idx]
        dr = device_results[idx]
        username, password = device_creds[idx]
        profile = device_profiles[idx]

        result = provision_device(
            dev, username, password, config, console,
            headless=True, tracker=dr.tracker,
            dry_run=(action == "dry_run"),
            profile_name=profile,
        )
        dr.success, _, dr.results = result  # type: ignore[misc]

    _clear()
    with Live(display, console=console, refresh_per_second=8):
        with ThreadPoolExecutor(max_workers=len(devices)) as pool:
            futures = [pool.submit(_worker, i) for i in range(len(devices))]
            while not all(f.done() for f in futures):
                time.sleep(0.25)
            for f in futures:
                f.result()

    return device_results


# --------------------------------------------------------------------------- #
#  Glob path resolution helper
# --------------------------------------------------------------------------- #


def _resolve_glob_path(path: str, console: Console) -> str | None:
    """Resolve a path that may contain glob wildcards to the latest matching file.

    If *path* contains no glob characters it is returned unchanged. When it
    does contain wildcards the pattern is expanded and the most recently
    modified matching file is returned. Returns ``None`` when the pattern
    matches nothing.
    """
    if not any(c in path for c in ("*", "?", "[")):
        return path
    expanded = str(_Path(path).expanduser())
    matches = sorted(
        (p for p in _glob_module.glob(expanded) if _Path(p).is_file()),
        key=lambda p: _Path(p).stat().st_mtime,
        reverse=True,
    )
    if not matches:
        console.print(f"[red]No files match pattern: {path}[/red]")
        return None
    resolved = matches[0]
    console.print(f"[dim]Glob resolved → {resolved}[/dim]")
    return resolved


# --------------------------------------------------------------------------- #
#  Upload Program flow
# --------------------------------------------------------------------------- #


def _flow_upload_program(config: Config) -> Config:
    """Upload a program file to a processor and load it."""
    _header("Upload Program")

    hosts_input = questionary.text(
        "Processor hostname(s) or IP(s) (comma-separated):"
    ).ask()
    if not hosts_input:
        return config
    hosts = [h.strip() for h in hosts_input.split(",") if h.strip()]

    creds = _prompt_credentials(config)
    if not creds:
        return config
    username, password = creds

    default_path = config.last_program_file or ""
    console.print("[dim]Tip: you can use a glob pattern (e.g. ~/builds/MyApp_*.lpz) to always pick the latest matching file.[/dim]")
    program_path = questionary.path(
        "Program file path:",
        default=default_path,
    ).ask()
    if not program_path:
        return config

    slot_input = questionary.text("Program slot:", default="1").ask()
    if not slot_input:
        return config
    try:
        slot = int(slot_input)
        if slot < 1:
            raise ValueError
    except ValueError:
        console.print("[red]Invalid slot number.[/red]")
        _pause()
        return config

    # Remember the program file (or glob pattern) for next time
    config.last_program_file = program_path
    save_config(config)

    resolved_path = _resolve_glob_path(program_path, console)
    if not resolved_path:
        _pause()
        return config

    if len(hosts) == 1:
        upload_program(hosts[0], username, password, resolved_path, slot, console, use_key_auth=config.ssh_key_auth)
        _pause()
    else:
        devices = [Device(ip=h) for h in hosts]
        device_results = _run_parallel(
            "program", devices, username, password, config,
            program_path=resolved_path, slot=slot,
        )
        _show_parallel_summary(device_results, config)
    return config


# --------------------------------------------------------------------------- #
#  Deploy Project (UC Engine) flow
# --------------------------------------------------------------------------- #


def _is_uc_engine(model: str) -> bool:
    """Check if a model string indicates a UC Engine device."""
    upper = model.upper()
    return upper.startswith("UC-") or upper == "UC-ENGINE"


def _deploy_project_single(
    host: str,
    username: str,
    password: str,
    project_path: str,
    con: Console,
) -> None:
    """Deploy a CH5Z project to a single UC Engine with progress display."""
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

    from .ctp import CrestronCTP

    local = _Path(project_path).expanduser()
    file_size = local.stat().st_size

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total} bytes"),
            console=con,
        ) as progress:
            task_id = progress.add_task(
                f"Connecting to {host}…", total=file_size, completed=0,
            )
            ctp = CrestronCTP(host, username, password)
            ctp.connect()
            progress.update(task_id, description=f"Uploading {local.name}…")

            def _progress_cb(sent: int, total: int) -> None:
                progress.update(task_id, completed=sent)

            ctp.upload_project(local, progress_callback=_progress_cb)
            progress.update(task_id, completed=file_size)

        ctp.disconnect()
        con.print(f"[green][OK][/green] Project deployed to {host}")

    except Exception as e:
        con.print(f"[red][FAIL][/red] Deploy to {host} failed: {e}")


def _deploy_project_worker(
    host: str,
    username: str,
    password: str,
    project_path: str,
    tracker: _StepTracker,
) -> bool:
    """Deploy a CH5Z project in headless mode (for parallel execution)."""
    from pathlib import Path as _Path

    from .ctp import CrestronCTP

    local = _Path(project_path).expanduser()

    try:
        tracker.start("Upload")
        ctp = CrestronCTP(host, username, password)
        ctp.connect()

        def _progress_cb(sent: int, total: int) -> None:
            pct = int(100 * sent / total) if total else 0
            tracker.update(f"Upload ({pct}%)")

        ctp.upload_project(local, progress_callback=_progress_cb)
        tracker.ok("Upload")
        ctp.disconnect()
        return True

    except Exception as e:
        tracker.fail(str(e))
        return False


def _flow_deploy_project(config: Config) -> Config:
    """Deploy a CH5Z project file to one or more UC Engines."""
    _header("Deploy Project (UC Engine)")

    console.print(
        "[cyan][INFO][/cyan] Deploys a CH5Z project to UC Engine devices "
        "via CTP/TLS (port 41797).\n"
    )

    # Target devices — comma-separated IPs or hostnames
    hosts_input = questionary.text(
        "UC Engine hostname(s) or IP(s) (comma-separated):"
    ).ask()
    if not hosts_input:
        return config
    hosts = [h.strip() for h in hosts_input.split(",") if h.strip()]

    creds = _prompt_credentials(config)
    if not creds:
        return config
    username, password = creds

    default_path = config.last_project_file or ""
    console.print("[dim]Tip: you can use a glob pattern (e.g. ~/builds/MyApp_*.ch5z) to always pick the latest matching file.[/dim]")
    project_path = questionary.path(
        "CH5Z project file path:",
        default=default_path,
    ).ask()
    if not project_path:
        return config

    # Remember the project file (or glob pattern) for next time
    config.last_project_file = project_path
    save_config(config)

    resolved_project = _resolve_glob_path(project_path, console)
    if not resolved_project:
        _pause()
        return config

    if not _Path(resolved_project).expanduser().is_file():
        console.print("[red]File not found.[/red]")
        _pause()
        return config

    if len(hosts) == 1:
        _deploy_project_single(hosts[0], username, password, resolved_project, console)
    else:
        # Parallel deployment
        devices = [Device(ip=h) for h in hosts]
        device_results = _run_parallel(
            "project", devices, username, password, config,
            project_path=resolved_project,
        )
        _show_parallel_summary(device_results, config)

    _pause()
    return config


# --------------------------------------------------------------------------- #
#  Restore & Erase flow
# --------------------------------------------------------------------------- #


def _flow_restore(config: Config) -> None:
    """Restore a device to factory defaults (initialize + restore)."""
    _header("Restore & Erase Device")
    console.print("[yellow][WARN][/yellow] This will erase all settings and programs "
                  "and restore the device to factory defaults.\n")

    host = questionary.text("Processor hostname or IP:").ask()
    if not host:
        return

    username = questionary.text("Admin username:").ask()
    if not username:
        return

    password = questionary.password("Admin password:").ask()
    if not password:
        return

    confirm = questionary.confirm(
        f"Are you sure you want to erase and restore {host}?",
        default=False,
    ).ask()
    if not confirm:
        console.print("[dim]Cancelled.[/dim]")
        _pause()
        return

    device = Device(ip=host)
    restore_device(device, username, password, console, use_key_auth=config.ssh_key_auth)
    _pause()


# --------------------------------------------------------------------------- #
#  Firmware audit flow
# --------------------------------------------------------------------------- #


def _flow_firmware_audit(config: Config) -> None:
    """Discover devices and compare firmware versions against available updates."""
    import re
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from dataclasses import dataclass

    from .firmware import (
        _parse_puf_metadata,
        find_local_firmware,
        query_firmware_server,
        version_compare,
    )
    from .ssh import CrestronSSH, sftp_upload

    _header("Firmware Audit")
    devices = discover_devices(config, console)

    if not devices:
        console.print(
            "[yellow]No devices found.[/yellow] "
            "Make sure you're on the same subnet and running with "
            "elevated privileges (sudo)."
        )
        _pause()
        return

    # Need credentials to read full PUF version via VER -V.
    # Check first-boot state for all devices first (in parallel).
    _check_first_boot_states(devices, config)
    first_boot_devices = [d for d in devices if d.is_first_boot]
    ready_devices = [d for d in devices if not d.is_first_boot]

    if first_boot_devices:
        names = ", ".join(d.ip for d in first_boot_devices)
        console.print(
            f"\n[yellow][WARN][/yellow] {len(first_boot_devices)} device(s) are in "
            f"first-boot mode ({names}).\n"
            "These have no credentials configured and will be shown with the "
            "discovery version only.\n"
            "Run [bold]Provision[/bold] first to create an account.\n"
        )

    if not ready_devices and not first_boot_devices:
        console.print("[dim]No devices to audit.[/dim]")
        _pause()
        return

    if ready_devices:
        creds = _prompt_credentials(config)
        if not creds:
            return
        username, password = creds
    else:
        username, password = "", ""

    console.print()
    console.print(f"[cyan][INFO][/cyan] {len(devices)} device(s) found. Reading firmware versions…")
    console.print()

    @dataclass
    class _AuditResult:
        device: Device
        current_version: str = ""
        available_version: str = ""
        available_path: str = ""
        source: str = ""  # where available firmware was found
        status: str = ""
        detail: str = ""

    def _audit_device(dev: Device) -> _AuditResult:
        host = dev.ip or dev.hostname
        result = _AuditResult(device=dev)

        # First-boot devices: use discovery version only
        if dev.is_first_boot:
            result.current_version = dev.firmware_version or ""
            if not result.current_version:
                result.status = "first-boot"
                result.detail = "First boot — no version"
                return result
            result.detail = "first boot (discovery version)"
        else:
            # SSH in to get the full PUF version from VER -V
            try:
                with CrestronSSH(host, username, password, use_key_auth=config.ssh_key_auth) as ssh:
                    if not dev.model:
                        dev.model = ssh.model
                    ver_output = ssh.send_command("VER -V", timeout=20)
                    for line in ver_output.splitlines():
                        if "PUF:" in line.upper() and "PUFEXEC" not in line.upper():
                            m = re.search(r"PUF:\s*([\d.]+)", line, re.IGNORECASE)
                            if m:
                                result.current_version = m.group(1)
                                break
            except Exception as e:
                # Fall back to discovery version if SSH fails
                if dev.firmware_version:
                    result.current_version = dev.firmware_version
                    result.detail = "version from discovery (SSH failed)"
                else:
                    result.status = "error"
                    result.detail = str(e)[:40]
                    return result

        if not result.current_version:
            result.current_version = dev.firmware_version or ""

        if not result.current_version:
            result.status = "unknown"
            result.detail = "Could not read version"
            return result

        # Find available firmware — check server API first (version only, no download)
        fw_model = dev.model or ""
        if not fw_model:
            result.status = "unknown"
            result.detail = "No model detected"
            return result

        fw_version = ""
        fw_path = None
        fw_source = ""

        # 1. Check firmware server API for version (no download needed)
        if config.firmware_server:
            server_info = query_firmware_server(fw_model, config.firmware_server)
            if server_info:
                fw_version = server_info.version
                fw_source = "server"

        # 2. Check local files
        if not fw_version:
            fw_path, fw_version = find_local_firmware(fw_model, config)
            if fw_version:
                fw_source = "local"

        # 3. Try downloading quietly
        if not fw_version:
            fw_path, _dl_msg = download_firmware_quiet(fw_model, config)
            if fw_path:
                fw_version, _ = _parse_puf_metadata(fw_path)
                # download_firmware_quiet tries server first, then direct URL
                fw_source = "downloaded"

        if not fw_version:
            result.status = "unknown"
            result.detail = "No firmware available"
            return result

        result.available_version = fw_version
        result.available_path = fw_path.name if fw_path else "(server)"
        result.source = fw_source

        cmp = version_compare(fw_version, result.current_version)
        if cmp == 0:
            result.status = "up-to-date"
        elif cmp > 0:
            result.status = "update-available"
        else:
            result.status = "newer"

        return result

    results: list[_AuditResult] = []
    with ThreadPoolExecutor(max_workers=min(len(devices), 8)) as pool:
        futures = {pool.submit(_audit_device, dev): dev for dev in devices}
        for future in as_completed(futures):
            results.append(future.result())

    # Sort: updates first, then first-boot, then errors, then up-to-date
    status_order = {"update-available": 0, "first-boot": 1, "error": 2, "unknown": 3, "newer": 4, "up-to-date": 5}
    results.sort(key=lambda r: (status_order.get(r.status, 6), r.device.ip))

    # Display results
    _clear()
    _banner()

    updates_available = sum(1 for r in results if r.status == "update-available")
    up_to_date = sum(1 for r in results if r.status == "up-to-date")
    first_boot_count = sum(1 for r in results if r.status == "first-boot")
    errors = sum(1 for r in results if r.status in ("error", "unknown"))

    table = Table(
        title="Firmware Audit Results",
        border_style="cyan",
        show_lines=False,
    )
    table.add_column("Device", style="cyan", min_width=16)
    table.add_column("Model", min_width=10)
    table.add_column("Current", min_width=16)
    table.add_column("Available", min_width=16)
    table.add_column("Source", min_width=10)
    table.add_column("Status", min_width=18)

    for r in results:
        host = r.device.ip or r.device.hostname
        model = r.device.model or "—"
        current = r.current_version or "—"

        # Format source label
        source_labels = {
            "server": "[cyan]Server API[/cyan]",
            "local": "[green]Local[/green]",
            "downloaded": "[yellow]Downloaded[/yellow]",
        }
        source = source_labels.get(r.source, "—")

        if r.status == "update-available":
            available = f"[yellow]{r.available_version}[/yellow]"
            status = "[yellow]⬆ Update Available[/yellow]"
        elif r.status == "up-to-date":
            available = r.available_version or "—"
            status = "[green]✓ Up to Date[/green]"
        elif r.status == "newer":
            available = r.available_version or "—"
            status = "[cyan]✓ Newer on Device[/cyan]"
        elif r.status == "first-boot":
            available = "—"
            status = "[yellow]⚠ First Boot[/yellow]"
        elif r.status == "error":
            available = "—"
            status = f"[red]✗ {r.detail}[/red]"
        else:
            available = "—"
            status = f"[dim]{r.detail}[/dim]"

        table.add_row(host, model, current, available, source, status)

    console.print(table)
    console.print()

    # Summary
    summary_parts = []
    if updates_available:
        summary_parts.append(f"[yellow]{updates_available} update(s) available[/yellow]")
    if up_to_date:
        summary_parts.append(f"[green]{up_to_date} up to date[/green]")
    if first_boot_count:
        summary_parts.append(f"[yellow]{first_boot_count} first boot (needs provisioning)[/yellow]")
    if errors:
        summary_parts.append(f"[dim]{errors} could not be checked[/dim]")
    console.print("  ".join(summary_parts))
    console.print()
    console.print(f"[dim]{len(results)} device(s) scanned. No changes were made.[/dim]")
    console.print()

    # Offer to update devices that have firmware available
    updatable = [r for r in results if r.status == "update-available"]
    up_to_date_with_fw = [r for r in results if r.status in ("up-to-date", "newer") and r.available_version]
    forceable = updatable + up_to_date_with_fw

    if not forceable:
        _pause()
        return

    # Ask if the user wants to push firmware
    update_choices: list[questionary.Choice] = []
    if updatable:
        update_choices.append(questionary.Choice(
            f"Update {len(updatable)} device(s) with available updates",
            value="update",
        ))
    if forceable:
        update_choices.append(questionary.Choice(
            "Force firmware on selected devices (including up-to-date)",
            value="force",
        ))
    update_choices.append(questionary.Choice("No, just view results", value="skip"))

    update_action = questionary.select(
        "Push firmware to devices?", choices=update_choices,
    ).ask()

    if not update_action or update_action == "skip":
        _pause()
        return

    # Pick which devices to update
    if update_action == "update":
        candidates = updatable
    else:
        candidates = forceable

    if len(candidates) == 1:
        targets = candidates
    else:
        dev_choices = [
            questionary.Choice(
                f"{(r.device.ip or r.device.hostname):<17} {r.device.model or '?':<10} "
                f"v{r.current_version} → v{r.available_version}  ({r.status})",
                value=r,
                checked=r.status == "update-available",
            )
            for r in candidates
        ]
        targets = questionary.checkbox(
            "Select devices to update:", choices=dev_choices,
        ).ask()
        if not targets:
            console.print("[dim]No devices selected.[/dim]")
            _pause()
            return

    # Download firmware files as needed, then upload to each device
    console.print()

    def _update_device(r: _AuditResult) -> tuple[str, bool, str]:
        """Download (if needed) and upload firmware to one device.

        Returns (host, success, detail).
        """
        host = r.device.ip or r.device.hostname
        model = (r.device.model or "").upper()

        # Find or download the firmware file
        fw_path, fw_ver = find_local_firmware(model, config)
        if not fw_path:
            fw_path, dl_msg = download_firmware_quiet(model, config)
            if not fw_path:
                return host, False, f"No firmware file: {dl_msg}"
            fw_ver, _ = _parse_puf_metadata(fw_path)

        # Upload via SFTP
        if not sftp_upload(
            host, username, password, str(fw_path), "/firmware",
            use_key_auth=config.ssh_key_auth,
        ):
            return host, False, "SFTP upload failed"

        # Trigger firmware install
        try:
            with CrestronSSH(host, username, password, use_key_auth=config.ssh_key_auth) as ssh:
                ssh.send_command("PUF", timeout=60)
        except Exception:
            pass  # PUF triggers reboot — connection drops

        ver_label = fw_ver or (fw_path.name if fw_path else "?")
        return host, True, f"v{ver_label} uploaded — installing (device will reboot)"

    from concurrent.futures import ThreadPoolExecutor, as_completed as _as_completed

    with console.status(
        f"Updating {len(targets)} device(s)…", spinner="dots",
    ):
        update_futures = {}
        with ThreadPoolExecutor(max_workers=min(len(targets), 8)) as pool:
            for r in targets:
                update_futures[pool.submit(_update_device, r)] = r
            update_results: list[tuple[str, bool, str]] = []
            for fut in _as_completed(update_futures):
                update_results.append(fut.result())

    console.print()
    for host, ok, detail in sorted(update_results, key=lambda x: x[0]):
        tag = "[green][OK][/green]" if ok else "[red][FAIL][/red]"
        console.print(f"  {tag} {host:<17} {detail}")
    console.print()

    _pause()


# --------------------------------------------------------------------------- #
#  Firmware download flow
# --------------------------------------------------------------------------- #


def _flow_firmware(config: Config) -> None:
    """Download firmware for a specific model."""
    _header("Download Firmware")
    available = list(config.firmware_urls.keys())
    if not available:
        console.print(
            "[yellow]No firmware URLs configured.[/yellow]\n"
            "Add entries under firmware_urls in your config.yaml.\n"
            "See config.example.yaml for the format."
        )
        _pause()
        return

    model = questionary.select(
        "Select model to download firmware for:",
        choices=available + ["Cancel"],
    ).ask()

    if not model or model == "Cancel":
        return

    # Check for existing local firmware first
    fw_path, fw_version = find_local_firmware(model, config)
    if fw_path:
        console.print(f"[cyan][INFO][/cyan] Local firmware found: {fw_path.name} (v{fw_version})")
        if not questionary.confirm("Download anyway?", default=False).ask():
            return

    download_firmware(model, config, console)
    _pause()


# --------------------------------------------------------------------------- #
#  Clear firmware cache flow
# --------------------------------------------------------------------------- #


def _flow_clear_cache() -> None:
    """Show cached firmware files and let the user delete them."""
    _header("Clear Firmware Cache")
    cache_dir, files = cache_info()

    if not files:
        console.print("[dim]Firmware cache is empty.[/dim]")
        console.print(f"[dim]Cache directory: {cache_dir}[/dim]")
        _pause()
        return

    total_size = sum(s for _, s in files)
    console.print(f"[bold]Cache directory:[/bold] {cache_dir}")
    console.print(f"[bold]Total size:[/bold] {total_size / 1_048_576:.1f} MB "
                  f"({len(files)} file{'s' if len(files) != 1 else ''})\n")

    choices = [
        questionary.Choice(
            f"{f.name}  ({size / 1_048_576:.1f} MB)",
            value=i,
        )
        for i, (f, size) in enumerate(files)
    ]

    action = questionary.select(
        "What to clear?",
        choices=[
            questionary.Choice("Delete all cached files", value="all"),
            questionary.Choice("Select files to delete", value="pick"),
            questionary.Choice("Cancel", value="cancel"),
        ],
    ).ask()

    if action is None or action == "cancel":
        return

    if action == "all":
        confirm = questionary.confirm(
            f"Delete all {len(files)} cached files ({total_size / 1_048_576:.1f} MB)?",
            default=False,
        ).ask()
        if confirm:
            count = clear_cache()
            console.print(f"[green][OK][/green] Deleted {count} file(s).")
    else:
        selected = questionary.checkbox(
            "Select files to delete:",
            choices=choices,
        ).ask()
        if selected:
            paths = [files[i][0] for i in selected]
            count = clear_cache(paths)
            console.print(f"[green][OK][/green] Deleted {count} file(s).")
        else:
            console.print("[dim]No files selected.[/dim]")

    _pause()


# --------------------------------------------------------------------------- #
#  Update flow
# --------------------------------------------------------------------------- #


def _flow_update() -> None:
    """Self-update the application binary."""
    global _update_info
    _header("Update")

    if not _update_info:
        console.print("[green]Already up to date.[/green]")
        _pause()
        return

    latest, url = _update_info
    console.print(f"[cyan][INFO][/cyan] Current version: v{__version__}")
    console.print(f"[cyan][INFO][/cyan] Latest version:  v{latest}")
    console.print(f"[cyan][INFO][/cyan] Release: {url}")
    console.print()

    confirm = questionary.confirm(
        f"Download and install v{latest}?", default=True
    ).ask()
    if not confirm:
        return

    if self_update(console):
        _update_info = None  # Clear notification after successful update
        _pause()
    else:
        _pause()


# --------------------------------------------------------------------------- #
#  Certificate Management flow
# --------------------------------------------------------------------------- #


def _flow_cert_management(config: Config) -> Config:
    """Certificate management submenu."""
    while True:
        _header("Certificate Management")
        choice = questionary.select(
            "Certificate Management",
            choices=[
                questionary.Choice("View Certificate Status", value="status"),
                questionary.Choice("Generate CSR", value="csr"),
                questionary.Choice("Install Certificate", value="install"),
                questionary.Choice("SSL/TLS Settings", value="tls"),
                questionary.Choice("Back", value="back"),
            ],
        ).ask()

        if choice is None or choice == "back":
            return config
        elif choice == "status":
            _flow_cert_status(config)
        elif choice == "csr":
            _flow_generate_csr(config)
        elif choice == "install":
            _flow_install_cert(config)
        elif choice == "tls":
            _flow_tls_settings(config)


def _flow_cert_status(config: Config) -> None:
    """View SSL mode and installed certificates on a device."""
    from .ssh import CrestronSSH

    _header("Certificate Status")
    host = questionary.text("Processor hostname or IP:").ask()
    if not host:
        return

    creds = _prompt_credentials(config)
    if not creds:
        return
    username, password = creds

    with console.status("Reading certificate info…", spinner="dots"):
        try:
            with CrestronSSH(host, username, password, use_key_auth=config.ssh_key_auth) as ssh:
                ssl_output = ssh.send_command("SSL", timeout=10)
                ws_certs = ssh.send_command("CERTIFICATE LISTN WEBSERVER", timeout=10)
                root_certs = ssh.send_command("CERTIFICATE LISTN ROOT", timeout=10)
                inter_certs = ssh.send_command("CERTIFICATE LISTN INTERMEDIATE", timeout=10)
        except Exception as e:
            console.print(f"[red][FAIL][/red] Connection failed: {e}")
            _pause()
            return

    # Display SSL mode
    console.print()
    console.print(Panel(
        ssl_output.strip() or "[dim]No SSL info returned[/dim]",
        title=f"SSL Status — {host}",
        border_style="cyan",
        padding=(1, 2),
    ))

    # Display webserver certs
    _cert_table("Webserver Certificates", ws_certs)
    _cert_table("Intermediate CA Certificates", inter_certs)
    _cert_table("Root CA Certificates", root_certs)

    _pause()


def _cert_table(title: str, raw_output: str) -> None:
    """Display certificate list output in a panel."""
    content = raw_output.strip()
    if not content or "no certificates" in content.lower() or content.startswith("Error"):
        console.print(f"\n[dim]{title}: None installed[/dim]")
        return
    console.print()
    console.print(Panel(
        content,
        title=title,
        border_style="cyan",
        padding=(1, 2),
    ))


def _flow_generate_csr(config: Config) -> None:
    """Generate a Certificate Signing Request on a device."""
    from pathlib import Path

    from .ssh import CrestronSSH, sftp_download

    _header("Generate CSR")
    host = questionary.text("Processor hostname or IP:").ask()
    if not host:
        return

    creds = _prompt_credentials(config)
    if not creds:
        return
    username, password = creds

    # Prompt for CSR fields with defaults from config
    csr = config.csr_defaults
    console.print("[dim]Fill in CSR details (press Enter to use default).[/dim]\n")

    country = questionary.text("Country (2-letter code):", default=csr.country).ask()
    if country is None:
        return
    state = questionary.text("State/Province:", default=csr.state).ask()
    if state is None:
        return
    locality = questionary.text("Locality/City:", default=csr.locality).ask()
    if locality is None:
        return
    org = questionary.text("Organization:", default=csr.organization).ask()
    if org is None:
        return
    ou = questionary.text("Organizational Unit:", default=csr.organizational_unit).ask()
    if ou is None:
        return
    cn = questionary.text("Common Name (hostname/domain):", default=host).ask()
    if cn is None:
        return
    email = questionary.text("Email:", default=csr.email).ask()
    if email is None:
        return

    # Subject Alternative Names
    san_input = questionary.text(
        "Subject Alt Names (comma-separated DNS names, or blank):",
        default=f"DNS:{cn}" if cn else "",
    ).ask()
    if san_input is None:
        return

    # Build SANs list
    sans: list[str] = []
    if san_input.strip():
        for s in san_input.split(","):
            s = s.strip()
            if s and not s.upper().startswith("DNS:"):
                s = f"DNS:{s}"
            if s:
                sans.append(s)

    # Build CREATECSR command
    # Format: CREATECSR C:ST:L:O:OU:CN:E [-I:true] [-S:altname,altname,...]
    parts = [
        country.strip() or " ",
        state.strip() or " ",
        locality.strip() or " ",
        org.strip() or " ",
        ou.strip() or " ",
        cn.strip() or " ",
        email.strip() or " ",
    ]
    # Quote values with spaces
    quoted = []
    for p in parts:
        if " " in p.strip():
            quoted.append(f'"{p}"')
        else:
            quoted.append(p)

    cmd = f"CREATECSR {':'.join(quoted)} -I:true"
    if sans:
        san_str = ",".join(sans)
        cmd += f" -S:{san_str}"

    console.print(f"\n[cyan]Command:[/cyan] {cmd}\n")

    confirm = questionary.confirm("Send this CSR command to the device?").ask()
    if not confirm:
        return

    # Execute on device
    try:
        with CrestronSSH(host, username, password, use_key_auth=config.ssh_key_auth) as ssh:
            with console.status("Generating CSR on device…", spinner="dots"):
                output = ssh.send_command(cmd, timeout=30)
            console.print(output.strip())
    except Exception as e:
        console.print(f"[red][FAIL][/red] Failed: {e}")
        _pause()
        return

    # Offer to download the CSR file
    console.print()
    download = questionary.confirm(
        "Download the CSR file from the device?"
    ).ask()
    if download:
        save_dir = questionary.path(
            "Save CSR to directory:",
            default=str(Path.home() / "Downloads"),
            only_directories=True,
        ).ask()
        if save_dir:
            # CSR is typically saved to /user/ on the device
            result = sftp_download(
                host, username, password,
                "/user/csr.pem", save_dir, console=console,
                use_key_auth=config.ssh_key_auth,
            )
            if result:
                console.print(f"[green][OK][/green] CSR saved: {result}")

    _pause()


def _flow_install_cert(config: Config) -> None:
    """Upload and install certificates on a device."""
    from pathlib import Path

    from .ssh import CrestronSSH, sftp_upload

    _header("Install Certificate")
    host = questionary.text("Processor hostname or IP:").ask()
    if not host:
        return

    creds = _prompt_credentials(config)
    if not creds:
        return
    username, password = creds

    # Certificate file
    cert_default = config.certificates.cert_file
    cert_path = questionary.path(
        "Certificate file (.pem, .cer, .crt, .pfx, .p12):",
        default=cert_default,
    ).ask()
    if not cert_path:
        return

    cert_file = Path(cert_path).expanduser()
    if not cert_file.is_file():
        console.print(f"[red][FAIL][/red] File not found: {cert_file}")
        _pause()
        return

    cert_ext = cert_file.suffix.lower()
    needs_password = cert_ext in (".pfx", ".p12")

    key_password = ""
    if needs_password:
        key_password = questionary.password(
            "Private key password (for PFX/P12):"
        ).ask() or ""

    # Optional intermediate cert
    inter_default = config.certificates.intermediate_file
    inter_path = questionary.path(
        "Intermediate CA cert (blank to skip):",
        default=inter_default,
    ).ask()

    # Optional root CA cert
    root_default = config.certificates.root_ca_file
    root_path = questionary.path(
        "Root CA cert (blank to skip):",
        default=root_default,
    ).ask()

    console.print()
    console.print("[bold]Installation plan:[/bold]")
    console.print(f"  Certificate:   {cert_file.name} → WEBSERVER store")
    if inter_path and Path(inter_path).expanduser().is_file():
        console.print(f"  Intermediate:  {Path(inter_path).name} → INTERMEDIATE store")
    if root_path and Path(root_path).expanduser().is_file():
        console.print(f"  Root CA:       {Path(root_path).name} → ROOT store")
    console.print("  SSL mode:      CA (activate CA-signed)")
    console.print()

    confirm = questionary.confirm("Proceed with installation?").ask()
    if not confirm:
        return

    try:
        # Upload cert file
        console.print("\n[cyan]Uploading certificate file…[/cyan]")
        if not sftp_upload(host, username, password, str(cert_file), "/user", console, use_key_auth=config.ssh_key_auth):
            _pause()
            return

        # Upload intermediate cert if provided
        if inter_path:
            inter_file = Path(inter_path).expanduser()
            if inter_file.is_file():
                console.print("\n[cyan]Uploading intermediate CA…[/cyan]")
                sftp_upload(host, username, password, str(inter_file), "/user", console, use_key_auth=config.ssh_key_auth)

        # Upload root CA if provided
        if root_path:
            root_file = Path(root_path).expanduser()
            if root_file.is_file():
                console.print("\n[cyan]Uploading root CA…[/cyan]")
                sftp_upload(host, username, password, str(root_file), "/user", console, use_key_auth=config.ssh_key_auth)

        # Install via SSH commands
        with CrestronSSH(host, username, password, use_key_auth=config.ssh_key_auth) as ssh:
            # Install root CA first (if provided)
            if root_path:
                root_file = Path(root_path).expanduser()
                if root_file.is_file():
                    console.print("\n[cyan]Installing root CA into ROOT store…[/cyan]")
                    out = ssh.send_command(
                        f"CERTIFICATE ADDF {root_file.name} ROOT", timeout=30
                    )
                    console.print(f"  {out.strip()}")

            # Install intermediate (if provided)
            if inter_path:
                inter_file = Path(inter_path).expanduser()
                if inter_file.is_file():
                    console.print("\n[cyan]Installing intermediate into INTERMEDIATE store…[/cyan]")
                    out = ssh.send_command(
                        f"CERTIFICATE ADDF {inter_file.name} INTERMEDIATE", timeout=30
                    )
                    console.print(f"  {out.strip()}")

            # Install webserver cert
            console.print("\n[cyan]Installing certificate into WEBSERVER store…[/cyan]")
            addf_cmd = f"CERTIFICATE ADDF {cert_file.name} WEBSERVER"
            if needs_password and key_password:
                addf_cmd += f" {key_password}"
            out = ssh.send_command(addf_cmd, timeout=30)
            console.print(f"  {out.strip()}")

            # Activate CA-signed SSL
            console.print("\n[cyan]Activating CA-signed SSL…[/cyan]")
            ssl_cmd = "SSL CA"
            if needs_password and key_password:
                ssl_cmd += f" -P:{key_password}"
            out = ssh.send_command(ssl_cmd, timeout=30)
            console.print(f"  {out.strip()}")

            console.print("\n[green][OK][/green] Certificate installation complete.")

    except Exception as e:
        console.print(f"\n[red][FAIL][/red] Installation failed: {e}")

    _pause()


def _flow_tls_settings(config: Config) -> None:
    """View and configure SSL/TLS settings on a device."""
    from .ssh import CrestronSSH

    _header("SSL/TLS Settings")
    host = questionary.text("Processor hostname or IP:").ask()
    if not host:
        return

    creds = _prompt_credentials(config)
    if not creds:
        return
    username, password = creds

    try:
        with CrestronSSH(host, username, password, use_key_auth=config.ssh_key_auth) as ssh:
            # Read current settings
            with console.status("Reading TLS settings…", spinner="dots"):
                ssl_out = ssh.send_command("SSL", timeout=10)
                tls_ver = ssh.send_command("TLSVERSION", timeout=10)
                ssl_verify = ssh.send_command("SSLVERIFY", timeout=10)
                self_reboot = ssh.send_command("CERTIFICATE SELFEXPIREREBOOT", timeout=10)

            table = Table(title=f"SSL/TLS Settings — {host}", border_style="cyan")
            table.add_column("Setting", style="cyan", min_width=25)
            table.add_column("Current Value", min_width=40)

            table.add_row("SSL Mode", ssl_out.strip())
            table.add_row("TLS Version", tls_ver.strip())
            table.add_row("SSL Verify", ssl_verify.strip())
            table.add_row("Self-Signed Reboot", self_reboot.strip())

            console.print(table)
            console.print()

            # Offer to change settings
            action = questionary.select(
                "Configure a setting:",
                choices=[
                    questionary.Choice("Set TLS Version", value="tlsver"),
                    questionary.Choice("Set SSL Verify", value="sslverify"),
                    questionary.Choice("Self-Signed Cert Reboot", value="selfreboot"),
                    questionary.Choice("Back", value="back"),
                ],
            ).ask()

            if action == "tlsver":
                ver = questionary.select(
                    "Minimum TLS version:",
                    choices=[
                        questionary.Choice("TLS 1.2 + 1.3 (Both)", value="BOTH"),
                        questionary.Choice("TLS 1.2 only", value="TLS1.2"),
                        questionary.Choice("TLS 1.3 only", value="TLS1.3"),
                    ],
                ).ask()
                if ver:
                    out = ssh.send_command(f"TLSVERSION {ver}", timeout=10)
                    console.print(f"  {out.strip()}")

            elif action == "sslverify":
                mode = questionary.select(
                    "SSL verification mode:",
                    choices=[
                        questionary.Choice("All checks enabled", value="ALL"),
                        questionary.Choice("Trust check only", value="-T:ON"),
                        questionary.Choice("Off (allow self-signed)", value="-T:OFF"),
                    ],
                ).ask()
                if mode:
                    out = ssh.send_command(f"SSLVERIFY {mode}", timeout=10)
                    console.print(f"  {out.strip()}")

            elif action == "selfreboot":
                mode = questionary.select(
                    "Auto-reboot on self-signed cert expiry:",
                    choices=[
                        questionary.Choice("Enable", value="ENABLE"),
                        questionary.Choice("Disable", value="DISABLE"),
                    ],
                ).ask()
                if mode:
                    out = ssh.send_command(
                        f"CERTIFICATE SELFEXPIREREBOOT {mode}", timeout=10
                    )
                    console.print(f"  {out.strip()}")

    except Exception as e:
        console.print(f"[red][FAIL][/red] Connection failed: {e}")

    _pause()


def _flow_bulk_apply_settings(
    devices: list[Device],
    username: str,
    password: str,
    config: Config,
) -> Config:
    """Push a chosen subset of shared settings to many devices at once.

    Deliberately never prompts for — or sends — IP address, subnet mask,
    gateway or hostname: those are per-device identity and belong to the
    provisioning flow.  This is for the settings that are the same estate
    wide (DNS, NTP, timezone, ports, lockout policy, FIPS).
    """
    from .provisioning import apply_common_settings

    _header("Apply Common Settings")
    console.print(
        f"[cyan]{len(devices)}[/cyan] device(s) selected. "
        "IP settings are not touched.\n"
    )

    # Which settings to push. Nothing is pre-selected — an accidental Enter
    # must not push an estate-wide change.
    field_choices = [
        questionary.Choice(f"Timezone           (currently configured: "
                           f"{config.timezone} — {timezone_label(config.timezone)})",
                           value="timezone"),
        questionary.Choice(f"NTP server         ({config.ntp_server})",
                           value="ntp_server"),
        questionary.Choice("Sync date/time now", value="sync_time"),
        questionary.Choice(f"DNS servers        ({', '.join(config.dns_servers) or 'not set'})",
                           value="dns_servers"),
        questionary.Choice(f"Web port           ({config.web_port})",
                           value="web_port"),
        questionary.Choice(f"Secure web port    ({config.secure_web_port})",
                           value="secure_web_port"),
        questionary.Choice(f"User login attempts({config.user_login_attempts})",
                           value="user_login_attempts"),
        questionary.Choice(f"User lockout time  ({config.user_lockout_time})",
                           value="user_lockout_time"),
        questionary.Choice(f"Console login attempts ({config.login_attempts})",
                           value="login_attempts"),
        questionary.Choice(f"Console lockout time   ({config.lockout_time})",
                           value="lockout_time"),
        questionary.Choice(f"FIPS mode          ({config.fips_mode})",
                           value="fips_mode"),
    ]
    chosen = questionary.checkbox(
        "Select the settings to push:", choices=field_choices,
    ).ask()
    if not chosen:
        console.print("[dim]Nothing selected.[/dim]")
        return config

    settings = CommonSettings()

    if "timezone" in chosen:
        tz = questionary.select(
            "Timezone (type to filter):",
            choices=[questionary.Choice(lbl, value=tid)
                     for tid, lbl in timezone_choices()],
            default=config.timezone.zfill(3),
        ).ask()
        if tz is None:
            return config
        settings.timezone = tz

    if "ntp_server" in chosen:
        ntp = questionary.text("NTP server:", default=config.ntp_server).ask()
        if not ntp:
            return config
        settings.ntp_server = ntp.strip()

    settings.sync_time = "sync_time" in chosen

    if "dns_servers" in chosen:
        dns_input = questionary.text(
            "DNS servers (comma-separated):",
            default=", ".join(config.dns_servers),
        ).ask()
        entries = [d.strip() for d in (dns_input or "").split(",") if d.strip()]
        if not entries:
            # Blank must not be read as "remove every DNS server".
            console.print("[yellow][WARN][/yellow] No DNS servers given — "
                          "leaving DNS untouched.")
        else:
            invalid = [d for d in entries if not _is_ipv4(d)]
            if invalid:
                console.print(f"[red][FAIL][/red] Not valid IPv4: "
                              f"{', '.join(invalid)}")
                return config
            settings.dns_servers = entries
            settings.dns_mode = questionary.select(
                "How should existing DNS servers be handled?",
                choices=[
                    questionary.Choice(
                        "Replace — remove any server not in this list",
                        value="replace"),
                    questionary.Choice(
                        "Append — keep existing servers as well",
                        value="append"),
                ],
            ).ask() or "replace"

    # Numeric and free-text settings, defaulted from config
    for key, prompt, caster in (
        ("web_port", "Web port", int),
        ("secure_web_port", "Secure web port", int),
        ("user_login_attempts", "User login attempts", int),
        ("user_lockout_time", "User lockout time", str),
        ("login_attempts", "Console login attempts", int),
        ("lockout_time", "Console lockout time", str),
    ):
        if key not in chosen:
            continue
        raw = questionary.text(f"{prompt}:", default=str(getattr(config, key))).ask()
        if not raw:
            return config
        try:
            setattr(settings, key, caster(raw.strip()))
        except ValueError:
            console.print(f"[red][FAIL][/red] {prompt} must be a number.")
            return config

    if "fips_mode" in chosen:
        fips = questionary.select(
            "FIPS mode:",
            choices=[questionary.Choice("OFF", value="OFF"),
                     questionary.Choice("ON", value="ON")],
            default=config.fips_mode if config.fips_mode in ("ON", "OFF") else "OFF",
        ).ask()
        if fips is None:
            return config
        settings.fips_mode = fips

    if settings.is_empty:
        console.print("[dim]Nothing to apply.[/dim]")
        return config

    # Confirmation: show exactly what will be sent
    summary = Table(title="Settings to Push", border_style="cyan")
    summary.add_column("Setting", style="cyan", min_width=22)
    summary.add_column("Value", min_width=20)
    for label, value in _describe_common_settings(settings):
        summary.add_row(label, value)
    console.print(summary)
    console.print(
        f"\n[dim]Target: {len(devices)} device(s). "
        "IP address, mask, gateway and hostname are not modified.[/dim]"
    )
    if settings.needs_reboot:
        console.print("[yellow][WARN][/yellow] FIPS mode only takes effect "
                      "after a reboot — this flow does not reboot.")
    console.print()

    mode = questionary.select(
        "Run mode:",
        choices=[
            questionary.Choice("Apply to devices", value="apply"),
            questionary.Choice("Dry run (show commands, change nothing)",
                               value="dry_run"),
            questionary.Choice("Cancel", value="cancel"),
        ],
    ).ask()
    if mode is None or mode == "cancel":
        console.print("[dim]Cancelled.[/dim]")
        return config

    dry_run = mode == "dry_run"

    # Remember the DNS list for next time
    if settings.dns_servers and settings.dns_servers != config.dns_servers:
        config.dns_servers = list(settings.dns_servers)
        save_config(config)

    workers = max(1, min(len(devices), config.discovery_probe_workers))
    results = []
    label = "Previewing…" if dry_run else "Applying settings…"
    with console.status(label, spinner="dots"):
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [
                pool.submit(apply_common_settings, dev, username, password,
                            settings, config, dry_run)
                for dev in devices
            ]
            results = [f.result() for f in futures]

    title = "Dry Run — Commands That Would Be Sent" if dry_run else "Settings Push Results"
    table = Table(title=title, border_style="cyan")
    table.add_column("Device", style="cyan", min_width=16)
    table.add_column("Result", min_width=10)
    table.add_column("Detail", min_width=30)
    for r in results:
        status = "[green]✓ OK[/green]" if r.success else "[red]✗ Failed[/red]"
        table.add_row(r.host, status, r.detail)
    console.print(table)

    failed = [r for r in results if not r.success]
    console.print()
    console.print(
        f"[green]{len(results) - len(failed)} succeeded[/green]"
        + (f", [red]{len(failed)} failed[/red]" if failed else "")
    )

    # On a dry run, show the actual commands — this is also how you confirm
    # the DNS reconciliation read the device correctly.
    if dry_run:
        for r in results:
            if not r.commands:
                continue
            console.print(f"\n[bold]{r.host}[/bold]"
                          + (f"  [dim]current DNS: "
                             f"{', '.join(r.current_dns) or 'none detected'}[/dim]"
                             if settings.dns_servers else ""))
            for cmd in r.commands:
                console.print(f"  [yellow]→[/yellow] {cmd}")

    return config


def _describe_common_settings(settings: CommonSettings) -> list[tuple[str, str]]:
    """Render a CommonSettings bundle as (label, value) rows for display."""
    rows: list[tuple[str, str]] = []
    if settings.timezone is not None:
        rows.append(("Timezone",
                     f"{settings.timezone} — {timezone_label(settings.timezone)}"))
    if settings.ntp_server is not None:
        rows.append(("NTP server", settings.ntp_server))
    if settings.sync_time:
        rows.append(("Date/time", "sync to this computer's clock"))
    if settings.dns_servers is not None:
        rows.append((f"DNS servers ({settings.dns_mode})",
                     ", ".join(settings.dns_servers)))
    if settings.web_port is not None:
        rows.append(("Web port", str(settings.web_port)))
    if settings.secure_web_port is not None:
        rows.append(("Secure web port", str(settings.secure_web_port)))
    if settings.user_login_attempts is not None:
        rows.append(("User login attempts", str(settings.user_login_attempts)))
    if settings.user_lockout_time is not None:
        rows.append(("User lockout time", settings.user_lockout_time))
    if settings.login_attempts is not None:
        rows.append(("Console login attempts", str(settings.login_attempts)))
    if settings.lockout_time is not None:
        rows.append(("Console lockout time", settings.lockout_time))
    if settings.fips_mode is not None:
        rows.append(("FIPS mode", settings.fips_mode))
    return rows


def _is_ipv4(value: str) -> bool:
    """True when value is a dot-decimal IPv4 address."""
    parts = value.split(".")
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            return False
        if len(part) > 1 and part[0] == "0":
            return False
    return True


def _flow_bulk_deploy_cert(
    devices: list[Device],
    username: str,
    password: str,
    config: Config,
) -> None:
    """Deploy a certificate to multiple devices in parallel."""
    from pathlib import Path

    from .ssh import CrestronSSH, sftp_upload

    _header("Deploy Certificate to Devices")

    console.print(f"[cyan]{len(devices)}[/cyan] device(s) selected.\n")

    # Certificate file
    cert_default = config.certificates.cert_file
    cert_path = questionary.path(
        "Certificate file (.pem, .cer, .crt, .pfx, .p12):",
        default=cert_default,
    ).ask()
    if not cert_path:
        return

    cert_file = Path(cert_path).expanduser()
    if not cert_file.is_file():
        console.print(f"[red][FAIL][/red] File not found: {cert_file}")
        return

    cert_ext = cert_file.suffix.lower()
    needs_password = cert_ext in (".pfx", ".p12")

    key_password = ""
    if needs_password:
        key_password = questionary.password(
            "Private key password (for PFX/P12):"
        ).ask() or ""

    # Optional intermediate/root
    inter_path = questionary.path(
        "Intermediate CA cert (blank to skip):",
        default=config.certificates.intermediate_file,
    ).ask()

    root_path = questionary.path(
        "Root CA cert (blank to skip):",
        default=config.certificates.root_ca_file,
    ).ask()

    confirm = questionary.confirm(
        f"Deploy certificate to {len(devices)} device(s)?"
    ).ask()
    if not confirm:
        return

    # Deploy to each device
    results: list[tuple[str, bool, str]] = []

    def _deploy_one(dev: Device) -> tuple[str, bool, str]:
        host = dev.ip or dev.hostname
        try:
            # Upload files
            if not sftp_upload(host, username, password, str(cert_file), "/user", use_key_auth=config.ssh_key_auth):
                return host, False, "SFTP upload failed"

            if inter_path:
                inter = Path(inter_path).expanduser()
                if inter.is_file():
                    sftp_upload(host, username, password, str(inter), "/user", use_key_auth=config.ssh_key_auth)

            if root_path:
                root = Path(root_path).expanduser()
                if root.is_file():
                    sftp_upload(host, username, password, str(root), "/user", use_key_auth=config.ssh_key_auth)

            # Install via SSH
            with CrestronSSH(host, username, password, use_key_auth=config.ssh_key_auth) as ssh:
                if root_path:
                    root = Path(root_path).expanduser()
                    if root.is_file():
                        ssh.send_command(
                            f"CERTIFICATE ADDF {root.name} ROOT", timeout=30
                        )

                if inter_path:
                    inter = Path(inter_path).expanduser()
                    if inter.is_file():
                        ssh.send_command(
                            f"CERTIFICATE ADDF {inter.name} INTERMEDIATE", timeout=30
                        )

                addf_cmd = f"CERTIFICATE ADDF {cert_file.name} WEBSERVER"
                if needs_password and key_password:
                    addf_cmd += f" {key_password}"
                ssh.send_command(addf_cmd, timeout=30)

                ssl_cmd = "SSL CA"
                if needs_password and key_password:
                    ssl_cmd += f" -P:{key_password}"
                ssh.send_command(ssl_cmd, timeout=30)

            return host, True, "OK"
        except Exception as e:
            return host, False, str(e)[:60]

    with console.status("Deploying certificates…", spinner="dots"):
        with ThreadPoolExecutor(max_workers=len(devices)) as pool:
            futures = [pool.submit(_deploy_one, dev) for dev in devices]
            results = [f.result() for f in futures]

    # Show results
    table = Table(title="Certificate Deployment Results", border_style="cyan")
    table.add_column("Device", style="cyan", min_width=18)
    table.add_column("Result", min_width=10)
    table.add_column("Detail", min_width=30)

    for host, success, detail in results:
        status = "[green]✓ OK[/green]" if success else "[red]✗ Failed[/red]"
        table.add_row(host, status, detail)

    console.print(table)


# --------------------------------------------------------------------------- #
#  IP Table Management flow
# --------------------------------------------------------------------------- #

@dataclass
class _IPTableEntry:
    """Parsed IP table row."""
    cip_id: int
    entry_type: str
    status: str
    dev_id: str
    port: str
    address: str
    model: str
    description: str
    room_id: str


def _parse_ipt_output(raw: str) -> list[_IPTableEntry]:
    """Parse IPT -T output into structured entries.

    Handles two formats:
    - **Pipe-delimited** (processors): columns separated by ``|``
    - **Whitespace-delimited** (UC Engines): fixed-width columns with no ``|``

    The UC Engine format looks like::

        CIP_ID  Type   Status     DevID  Port   IP Address/SiteName     RoomID
            04  Gway    ONLINE        00  41794  10.100.203.139             (null)
    """
    entries: list[_IPTableEntry] = []
    lines = raw.splitlines()

    # Detect format: if any data-like line contains "|", use pipe parsing
    use_pipe = any("|" in ln and not ln.strip().startswith("---") for ln in lines)

    if use_pipe:
        in_data = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("---"):
                in_data = True
                continue
            if not in_data:
                continue
            if not stripped or "|" not in stripped:
                continue
            parts = [p.strip() for p in stripped.split("|")]
            if len(parts) < 6:
                continue
            try:
                cip_id = int(parts[0])
            except (ValueError, IndexError):
                continue
            entries.append(_IPTableEntry(
                cip_id=cip_id,
                entry_type=parts[1] if len(parts) > 1 else "",
                status=parts[2] if len(parts) > 2 else "",
                dev_id=parts[3] if len(parts) > 3 else "",
                port=parts[4] if len(parts) > 4 else "",
                address=parts[5] if len(parts) > 5 else "",
                model=parts[6] if len(parts) > 6 else "",
                description=parts[7] if len(parts) > 7 else "",
                room_id=parts[8] if len(parts) > 8 else "",
            ))
    else:
        # Whitespace-delimited (UC Engine format)
        header_seen = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.upper().startswith("CIP_ID"):
                header_seen = True
                continue
            if not header_seen:
                # Skip preamble lines like "IP Table:"
                continue
            parts = stripped.split()
            if len(parts) < 6:
                continue
            try:
                cip_id = int(parts[0])
            except (ValueError, IndexError):
                continue
            # Rejoin remaining fields after the first 6 as room_id
            # Format: CIP_ID Type Status DevID Port Address [RoomID...]
            room_id = " ".join(parts[6:]) if len(parts) > 6 else ""
            if room_id == "(null)":
                room_id = ""
            entries.append(_IPTableEntry(
                cip_id=cip_id,
                entry_type=parts[1],
                status=parts[2],
                dev_id=parts[3],
                port=parts[4],
                address=parts[5],
                model="",
                description="",
                room_id=room_id,
            ))
    return entries


def _display_ip_table(entries: list[_IPTableEntry], title: str = "IP Table") -> None:
    """Display parsed IP table entries in a rich table."""
    if not entries:
        console.print(f"\n[dim]{title}: No entries[/dim]\n")
        return

    table = Table(title=title, border_style="cyan", show_lines=False)
    table.add_column("CIP ID", style="bold", justify="right")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("Address / Hostname")
    table.add_column("Port", justify="right")
    table.add_column("Model")
    table.add_column("Description")

    online = 0
    for e in entries:
        if e.status.upper() == "ONLINE":
            status_str = "[green]ONLINE[/green]"
            online += 1
        elif e.status.upper() == "OFFLINE":
            status_str = "[red]OFFLINE[/red]"
        else:
            status_str = f"[dim]{e.status}[/dim]"

        table.add_row(
            str(e.cip_id),
            e.entry_type,
            status_str,
            e.address,
            e.port,
            e.model or "[dim]—[/dim]",
            e.description or "[dim]—[/dim]",
        )

    console.print()
    console.print(table)
    total = len(entries)
    console.print(
        f"[dim]  {total} {'entry' if total == 1 else 'entries'}, "
        f"{online} online[/dim]\n"
    )


def _ip_table_view(ssh: "_ConsoleConn") -> None:
    """Read and display the full IP table."""
    raw = ssh.send_command("IPT -T", timeout=15)
    entries = _parse_ipt_output(raw)
    _display_ip_table(entries)


def _ip_table_add_master(ssh: "_ConsoleConn") -> None:
    """Add a master entry to the IP table."""
    cip_id = questionary.text("CIP ID (e.g. 3):").ask()
    if not cip_id:
        return
    try:
        int(cip_id)
    except ValueError:
        console.print("[red][FAIL][/red] CIP ID must be a number.")
        return

    address = questionary.text("Hostname or IP address:").ask()
    if not address:
        return

    resp = ssh.send_command(f"ADDM {cip_id} {address}", timeout=10)
    if "set" in resp.lower():
        console.print(f"[green][OK][/green] Master entry added: ID {cip_id} → {address}")
    else:
        console.print(f"[yellow][WARN][/yellow] Response: {resp.strip()}")

    # Show updated table
    _ip_table_view(ssh)


def _ip_table_remove_master(ssh: "_ConsoleConn") -> None:
    """Remove master entries from the IP table."""
    raw = ssh.send_command("IPT -T", timeout=15)
    entries = _parse_ipt_output(raw)
    # Filter to gateway/master type entries
    masters = [e for e in entries if e.entry_type.upper() in ("GWAY", "MASTER", "GATEWAY")]
    if not masters:
        console.print("[dim]No master entries found.[/dim]")
        return

    choices = [
        questionary.Choice(
            f"ID {e.cip_id:>3}  {e.address:<40}  {e.status}",
            value=e,
        )
        for e in masters
    ]
    selected = questionary.checkbox(
        "Select entries to remove:", choices=choices,
    ).ask()
    if not selected:
        return

    for entry in selected:
        # Extract hostname/IP — address field may be "hostname(ip)"
        addr = entry.address.split("(")[0].strip() if "(" in entry.address else entry.address
        resp = ssh.send_command(f"REMM {entry.cip_id} {addr}", timeout=10)
        if "set" in resp.lower():
            console.print(f"[green][OK][/green] Removed: ID {entry.cip_id} — {addr}")
        else:
            console.print(f"[yellow][WARN][/yellow] ID {entry.cip_id}: {resp.strip()}")

    _ip_table_view(ssh)


def _ip_table_add_peer(ssh: "_ConsoleConn") -> None:
    """Add a peer entry to the IP table."""
    cip_id = questionary.text("CIP ID (e.g. 3):").ask()
    if not cip_id:
        return
    try:
        int(cip_id)
    except ValueError:
        console.print("[red][FAIL][/red] CIP ID must be a number.")
        return

    address = questionary.text("Hostname or IP address:").ask()
    if not address:
        return

    program = questionary.text("Program number:", default="1").ask()
    if not program:
        return

    resp = ssh.send_command(f"ADDPEER {cip_id} {address} -P:{program}", timeout=10)
    console.print(f"[cyan][INFO][/cyan] {resp.strip()}")

    _ip_table_view(ssh)


def _ip_table_remove_peer(ssh: "_ConsoleConn") -> None:
    """Remove peer entries from the IP table."""
    raw = ssh.send_command("IPT -T", timeout=15)
    entries = _parse_ipt_output(raw)
    # Filter to non-master entries
    peers = [e for e in entries if e.entry_type.upper() not in ("GWAY", "MASTER", "GATEWAY")]
    if not peers:
        console.print("[dim]No peer entries found.[/dim]")
        return

    choices = [
        questionary.Choice(
            f"ID {e.cip_id:>3}  {e.address:<40}  {e.status}  ({e.entry_type})",
            value=e,
        )
        for e in peers
    ]
    selected = questionary.checkbox(
        "Select entries to remove:", choices=choices,
    ).ask()
    if not selected:
        return

    program = questionary.text("Program number:", default="1").ask()
    if not program:
        return

    for entry in selected:
        addr = entry.address.split("(")[0].strip() if "(" in entry.address else entry.address
        resp = ssh.send_command(f"REMPEER {entry.cip_id} {addr} -P:{program}", timeout=10)
        console.print(f"[cyan][INFO][/cyan] ID {entry.cip_id}: {resp.strip()}")

    _ip_table_view(ssh)


def _ip_table_clear(ssh: "_ConsoleConn") -> None:
    """Clear the IP table."""
    program = questionary.text(
        "Program number to clear (leave blank for all):",
        default="",
    ).ask()
    if program is None:
        return

    label = f"program {program}" if program else "all programs"
    confirm = questionary.confirm(
        f"Clear ALL IP table entries for {label}?", default=False,
    ).ask()
    if not confirm:
        return

    cmd = f"IPTABLE -C -P:{program}" if program else "IPTABLE -C"
    resp = ssh.send_command(cmd, timeout=10)
    if resp.strip():
        console.print(f"[cyan][INFO][/cyan] {resp.strip()}")
    console.print(f"[green][OK][/green] IP table cleared ({label}).")
    _ip_table_view(ssh)


def _flow_ip_table(config: Config, host: str | None = None,
                   username: str | None = None,
                   password: str | None = None,
                   model: str | None = None) -> Config:
    """IP Table Management submenu with persistent SSH or CTP connection.

    Automatically uses CTP/TLS for UC Engine devices (UC-* models) since
    they don't expose SSH.
    """
    from .ssh import CrestronSSH

    _header("IP Table Management")

    if not host:
        host = questionary.text("Processor hostname or IP:").ask()
        if not host:
            return config

    if username is None or password is None:
        creds = _prompt_credentials(config)
        if not creds:
            return config
        username, password = creds

    # Determine transport: CTP for UC Engines, SSH for everything else
    use_ctp = model and _is_uc_engine(model)
    if not use_ctp and model is None:
        # No model hint — ask the user
        transport = questionary.select(
            "Connection type:",
            choices=[
                questionary.Choice("SSH (processors, touchpanels)", value="ssh"),
                questionary.Choice("CTP/TLS (UC Engines)", value="ctp"),
            ],
        ).ask()
        use_ctp = transport == "ctp"

    # Connect once, keep alive for the session
    try:
        if use_ctp:
            from .ctp import CrestronCTP
            conn = CrestronCTP(host, username, password)
            conn.connect()
        else:
            conn = CrestronSSH(host, username, password, use_key_auth=config.ssh_key_auth)
            conn.connect()
    except Exception as e:
        console.print(f"[red][FAIL][/red] Connection failed: {e}")
        _pause()
        return config

    console.print(f"[green][OK][/green] Connected to {host} ({conn.model})\n")

    try:
        while True:
            _header(f"IP Table — {host} ({conn.model})")
            choice = questionary.select(
                f"IP Table — {host}",
                choices=[
                    questionary.Choice("View IP Table", value="view"),
                    questionary.Choice("Add Master Entry", value="add_master"),
                    questionary.Choice("Remove Master Entry", value="rem_master"),
                    questionary.Choice("Add Peer Entry", value="add_peer"),
                    questionary.Choice("Remove Peer Entry", value="rem_peer"),
                    questionary.Choice("Clear IP Table", value="clear"),
                    questionary.Choice("Back", value="back"),
                ],
            ).ask()

            if choice is None or choice == "back":
                break

            try:
                if choice == "view":
                    _ip_table_view(conn)
                elif choice == "add_master":
                    _ip_table_add_master(conn)
                elif choice == "rem_master":
                    _ip_table_remove_master(conn)
                elif choice == "add_peer":
                    _ip_table_add_peer(conn)
                elif choice == "rem_peer":
                    _ip_table_remove_peer(conn)
                elif choice == "clear":
                    _ip_table_clear(conn)
            except Exception as e:
                console.print(f"[red][FAIL][/red] {e}")

            _pause()
    finally:
        try:
            conn.disconnect()
        except Exception:
            pass

    return config


# --------------------------------------------------------------------------- #
#  Account Management flow
# --------------------------------------------------------------------------- #


# Standard Crestron access levels (display names) and their group names.
# LISTUSERS shows singular access levels; ADDUSERTOGROUP needs plural group names.
ACCESS_LEVELS = ["Administrator", "Programmer", "Operator", "User", "Connect"]
_LEVEL_TO_GROUP = {
    "Administrator": "Administrators",
    "Programmer": "Programmers",
    "Operator": "Operators",
    "User": "Users",
    "Connect": "Connections",
}


@dataclass
class _UserInfo:
    """Parsed row from LISTUSERS pipe-delimited table."""
    username: str
    access_level: str
    groups: str


def _parse_listusers(raw: str) -> list[_UserInfo]:
    """Parse LISTUSERS pipe-delimited table output.

    Expected format:
        TableStart: [ User List ]
        User                 | Access Level         | Groups
        ---------------------+----------------------+---------------------
        admin                | Administrator        | Administrators
        mike                 | None                 |
    """
    users: list[_UserInfo] = []
    in_data = False
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Separator line marks the start of data rows
        if stripped.startswith("---") and "+" in stripped:
            in_data = True
            continue
        if not in_data:
            continue
        if "|" not in stripped:
            continue
        parts = [p.strip() for p in stripped.split("|")]
        if len(parts) < 2:
            continue
        username = parts[0]
        if not username:
            continue
        access_level = parts[1] if len(parts) > 1 else ""
        groups = parts[2] if len(parts) > 2 else ""
        users.append(_UserInfo(
            username=username,
            access_level=access_level if access_level.lower() != "none" else "",
            groups=groups,
        ))
    return users


def _list_users_from_device(ssh: "CrestronSSH") -> list[_UserInfo]:
    """Get the user list from the device via LISTUSERS."""
    raw = ssh.send_command("LISTUSERS", timeout=15)
    return _parse_listusers(raw)


def _account_list_users(ssh: "CrestronSSH") -> None:
    """List all users with their access levels and group memberships."""
    with console.status("Reading users…", spinner="dots"):
        users = _list_users_from_device(ssh)

    if not users:
        console.print("\n[dim]No users found.[/dim]\n")
        return

    table = Table(title="User Accounts", border_style="cyan", show_lines=False)
    table.add_column("Username", style="bold")
    table.add_column("Access Level")
    table.add_column("Groups")

    for user in users:
        level_style = {
            "Administrator": "[bold red]Administrator[/bold red]",
            "Programmer": "[bold yellow]Programmer[/bold yellow]",
            "Operator": "[cyan]Operator[/cyan]",
            "User": "[dim]User[/dim]",
            "Connect": "[dim]Connect[/dim]",
        }.get(user.access_level, "[dim]—[/dim]")

        table.add_row(
            user.username,
            level_style,
            user.groups if user.groups else "[dim]—[/dim]",
        )

    console.print()
    console.print(table)
    console.print(f"[dim]  {len(users)} user(s)[/dim]\n")


def _activate_new_account(host: str, username: str, password: str) -> None:
    """Log in as a newly created user to clear the expired-password prompt.

    Crestron marks ADDUSER passwords as temporary.  The first SSH login
    shows "Your temporary password is expired!" and prompts for a new
    password.  We automate this by re-setting the same password so the
    user can log in without interruption.
    """
    import paramiko
    from .ssh import _read_until, CONNECT_TIMEOUT

    console.print("[cyan][INFO][/cyan] Activating account…", end=" ")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            host, username=username, password=password,
            timeout=CONNECT_TIMEOUT, look_for_keys=False, allow_agent=False,
        )
    except Exception as exc:
        console.print(f"[yellow][WARN][/yellow] Could not activate: {exc}")
        return

    try:
        channel = client.invoke_shell(width=200, height=50)
        channel.settimeout(30)

        # Wait for either the expired-password prompt or a normal CLI prompt
        output = _read_until(channel, [b"Password:", b">"], timeout=15)

        if b"password" in output.lower() and b">" not in output:
            # Expired password flow — send new password
            channel.sendall(password.encode() + b"\r")
            output2 = _read_until(
                channel, [b"Verify", b"verify", b"Password:", b">"], timeout=10,
            )
            if b"verify" in output2.lower():
                channel.sendall(password.encode() + b"\r")
                _read_until(channel, [b">", b"successfully"], timeout=10)
            console.print("[green][OK][/green] Account activated.")
        else:
            # No expired-password prompt — already active
            console.print("[green][OK][/green] Account already active.")

        channel.close()
    except Exception as exc:
        console.print(f"[yellow][WARN][/yellow] Activation issue: {exc}")
    finally:
        client.close()


def _account_create_user(ssh: "CrestronSSH") -> None:
    """Create a new user account."""
    username = questionary.text("Username:").ask()
    if not username:
        return

    password = questionary.password("Password:").ask()
    if not password:
        return
    confirm_pw = questionary.password("Confirm password:").ask()
    if password != confirm_pw:
        console.print("[red][FAIL][/red] Passwords do not match.")
        return

    resp = ssh.send_command(f"ADDUSER -N:{username} -P:{password}", timeout=10)
    if "error" in resp.lower():
        console.print(f"[red][FAIL][/red] {resp.strip()}")
        return
    console.print(f"[green][OK][/green] User '{username}' created.")

    # Offer to set access level
    level = questionary.select(
        "Access level:",
        choices=[
            questionary.Choice("Administrator", value="Administrator"),
            questionary.Choice("Programmer", value="Programmer"),
            questionary.Choice("Operator", value="Operator"),
            questionary.Choice("User", value="User"),
            questionary.Choice("Connect", value="Connect"),
            questionary.Choice("Skip (no group assignment)", value=None),
        ],
    ).ask()

    if level:
        group = _LEVEL_TO_GROUP.get(level, level)
        resp = ssh.send_command(
            f"ADDUSERTOGROUP -N:{username} -G:{group}", timeout=10,
        )
        if "error" in resp.lower():
            console.print(f"[yellow][WARN][/yellow] Group assignment: {resp.strip()}")
        else:
            console.print(f"[green][OK][/green] Added to '{group}' group.")

    # Activate the account by logging in as the new user and confirming
    # the temporary password.  Crestron marks new passwords as expired,
    # so the first SSH login prompts "Password:" to set a new one.
    _activate_new_account(ssh.host, username, password)


def _account_delete_user(ssh: "CrestronSSH") -> None:
    """Delete a user account."""
    with console.status("Reading users…", spinner="dots"):
        users = _list_users_from_device(ssh)
    if not users:
        console.print("[dim]No users found.[/dim]")
        return

    choices = [questionary.Choice(u.username, value=u.username) for u in users]
    username = questionary.select("Select user to delete:", choices=choices).ask()
    if not username:
        return

    confirm = questionary.confirm(
        f"Delete user '{username}'? This cannot be undone.", default=False,
    ).ask()
    if not confirm:
        return

    resp = ssh.send_command(f"DELETEUSER {username} /Y", timeout=10)
    if "error" in resp.lower():
        console.print(f"[red][FAIL][/red] {resp.strip()}")
    else:
        console.print(f"[green][OK][/green] User '{username}' deleted.")


def _account_change_level(ssh: "CrestronSSH") -> None:
    """Change a user's access level (group membership)."""
    with console.status("Reading users…", spinner="dots"):
        users = _list_users_from_device(ssh)

    if not users:
        console.print("[dim]No users found.[/dim]")
        return

    # Show current levels in the selection
    choices = []
    for u in users:
        current = u.access_level or "None"
        choices.append(questionary.Choice(f"{u.username}  ({current})", value=u))

    selected = questionary.select("Select user:", choices=choices).ask()
    if not selected:
        return

    current_level = selected.access_level
    # Parse current groups into a list for removal
    current_group_list = [g.strip() for g in selected.groups.split(",") if g.strip()] if selected.groups else []

    new_level = questionary.select(
        f"New access level for '{selected.username}':",
        choices=[questionary.Choice(lvl, value=lvl) for lvl in ACCESS_LEVELS],
    ).ask()
    if not new_level:
        return

    if new_level == current_level:
        console.print(f"[dim]Already '{new_level}' — no change.[/dim]")
        return

    # Remove from current access-level groups
    for group in current_group_list:
        # Match both singular and plural group names
        group_lower = group.lower()
        is_access_group = any(
            group_lower == lvl.lower() or group_lower == g.lower()
            for lvl, g in _LEVEL_TO_GROUP.items()
        )
        if is_access_group:
            resp = ssh.send_command(
                f"REMOVEUSERFROMGROUP -N:{selected.username} -G:{group}", timeout=10,
            )
            if "error" in resp.lower():
                console.print(f"[yellow][WARN][/yellow] Remove from {group}: {resp.strip()}")

    # Add to new group
    new_group = _LEVEL_TO_GROUP.get(new_level, new_level)
    resp = ssh.send_command(
        f"ADDUSERTOGROUP -N:{selected.username} -G:{new_group}", timeout=10,
    )
    if "error" in resp.lower():
        console.print(f"[red][FAIL][/red] {resp.strip()}")
    else:
        console.print(f"[green][OK][/green] '{selected.username}' is now {new_level}.")


def _account_reset_password(ssh: "CrestronSSH") -> None:
    """Reset a user's password."""
    with console.status("Reading users…", spinner="dots"):
        users = _list_users_from_device(ssh)
    if not users:
        console.print("[dim]No users found.[/dim]")
        return

    choices = [questionary.Choice(u.username, value=u.username) for u in users]
    username = questionary.select("Select user:", choices=choices).ask()
    if not username:
        return

    password = questionary.password("New password:").ask()
    if not password:
        return
    confirm_pw = questionary.password("Confirm password:").ask()
    if password != confirm_pw:
        console.print("[red][FAIL][/red] Passwords do not match.")
        return

    resp = ssh.send_command(
        f"RESETPASSWORD -N:{username} -P:{password}", timeout=10,
    )
    if "error" in resp.lower():
        console.print(f"[red][FAIL][/red] {resp.strip()}")
    else:
        console.print(f"[green][OK][/green] Password reset for '{username}'.")


def _account_manage_pubkey(ssh: "CrestronSSH", config: Config,
                           host: str, login_user: str,
                           login_pass: str) -> None:
    """Upload an SSH public key and register it for a user."""
    from .ssh import sftp_upload

    with console.status("Reading users…", spinner="dots"):
        users = _list_users_from_device(ssh)
    if not users:
        console.print("[dim]No users found.[/dim]")
        return

    choices = [questionary.Choice(u.username, value=u.username) for u in users]
    username = questionary.select("Add SSH key for which user?", choices=choices).ask()
    if not username:
        return

    # Show existing keys
    try:
        existing = ssh.send_command(f"LISTPUBKEYFROMUSER -N:{username}", timeout=10)
        if existing.strip() and "error" not in existing.lower():
            console.print(f"\n[cyan][INFO][/cyan] Existing keys for '{username}':")
            console.print(f"  {existing.strip()}\n")
    except Exception:
        pass

    # Determine key file source
    default_key = config.pubkey_file or "~/.ssh/id_rsa.pub"
    key_source = questionary.text(
        "Public key file (local path or URL):",
        default=default_key,
    ).ask()
    if not key_source:
        return

    # Resolve the key file (handles URLs and local paths)
    from .provisioning import _resolve_pubkey
    key_path = _resolve_pubkey(key_source)
    if not key_path or not key_path.exists():
        console.print(f"[red][FAIL][/red] Key file not found: {key_source}")
        return

    # Upload the key file via SFTP to /user/
    console.print(f"  Uploading {key_path.name} to /user/…")
    if not sftp_upload(host, login_user, login_pass, str(key_path),
                       "/user", use_key_auth=config.ssh_key_auth):
        console.print("[red][FAIL][/red] Key upload failed.")
        return

    # Register the key with the user account
    resp = ssh.send_command(
        f"ADDPUBKEYTOUSER -N:{username} -K:{key_path.name}", timeout=10,
    )
    if "error" in resp.lower():
        console.print(f"[red][FAIL][/red] {resp.strip()}")
    else:
        console.print(f"[green][OK][/green] Public key registered for '{username}'.")

    # Clean up temp file if it was downloaded from a URL
    import tempfile
    if str(key_path).startswith(tempfile.gettempdir()):
        key_path.unlink(missing_ok=True)


def _account_locked_users(ssh: "CrestronSSH") -> None:
    """Display locked-out user accounts."""
    raw = ssh.send_command("LISTLOCKEDUSERS", timeout=10)

    # Extract usernames — handle both pipe-delimited tables and simple lists
    names: list[str] = []
    in_data = False
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Check for pipe-delimited table format
        if stripped.startswith("---") and ("+" in stripped or "-" in stripped):
            in_data = True
            continue
        if in_data and "|" in stripped:
            name = stripped.split("|")[0].strip()
            if name:
                names.append(name)
            continue
        if in_data and stripped:
            token = stripped.split()[0]
            if token:
                names.append(token)
            continue
        # Simple list format — skip headers and decorations
        if not in_data and "|" not in stripped:
            if stripped.startswith("-") or stripped.startswith("="):
                continue
            if stripped.upper().startswith("TABLESTART") or stripped.endswith(":"):
                continue
            if "no" in stripped.lower() and "locked" in stripped.lower():
                break
            token = stripped.split()[0]
            if token and token.upper() not in ("NO", "NONE", "ERROR"):
                names.append(token)

    if not names:
        console.print("\n[green][OK][/green] No locked-out users.\n")
        return

    table = Table(title="Locked Users", border_style="yellow")
    table.add_column("Username", style="bold red")
    for name in names:
        table.add_row(name)

    console.print()
    console.print(table)
    console.print()


def _flow_account_mgmt(config: Config, host: str | None = None,
                       username: str | None = None,
                       password: str | None = None) -> Config:
    """Account Management submenu with persistent SSH connection."""
    from .ssh import CrestronSSH

    _header("Account Management")

    if not host:
        host = questionary.text("Processor hostname or IP:").ask()
        if not host:
            return config

    if username is None or password is None:
        creds = _prompt_credentials(config)
        if not creds:
            return config
        username, password = creds

    try:
        ssh = CrestronSSH(host, username, password, use_key_auth=config.ssh_key_auth)
        ssh.connect()
    except Exception as e:
        console.print(f"[red][FAIL][/red] Connection failed: {e}")
        _pause()
        return config

    console.print(f"[green][OK][/green] Connected to {host} ({ssh.model})\n")

    try:
        while True:
            _header(f"Account Management — {host} ({ssh.model})")
            choice = questionary.select(
                f"Accounts — {host}",
                choices=[
                    questionary.Choice("List Users", value="list"),
                    questionary.Choice("Create User", value="create"),
                    questionary.Choice("Delete User", value="delete"),
                    questionary.Choice("Change Access Level", value="level"),
                    questionary.Choice("Reset Password", value="password"),
                    questionary.Choice("Add SSH Public Key", value="pubkey"),
                    questionary.Choice("View Locked Users", value="locked"),
                    questionary.Choice("Back", value="back"),
                ],
            ).ask()

            if choice is None or choice == "back":
                break

            try:
                if choice == "list":
                    _account_list_users(ssh)
                elif choice == "create":
                    _account_create_user(ssh)
                elif choice == "delete":
                    _account_delete_user(ssh)
                elif choice == "level":
                    _account_change_level(ssh)
                elif choice == "password":
                    _account_reset_password(ssh)
                elif choice == "pubkey":
                    _account_manage_pubkey(ssh, config, host, username, password)
                elif choice == "locked":
                    _account_locked_users(ssh)
            except Exception as e:
                console.print(f"[red][FAIL][/red] {e}")

            _pause()
    finally:
        try:
            ssh.disconnect()
        except Exception:
            pass

    return config


def _flow_settings(config: Config) -> Config:
    """View and edit configuration."""
    while True:
        _header("Settings")
        console.print("[bold]Current Settings[/bold]")
        console.print(f"  Timezone:            {config.timezone} — {timezone_label(config.timezone)}")
        console.print(f"  NTP Server:          {config.ntp_server}")
        console.print(f"  Public Key:          {config.pubkey_file}")
        console.print(f"  Firmware Directory:  {config.firmware_dir}")
        console.print(f"  Firmware Server:     {config.firmware_server or '(not configured)'}")
        console.print(f"  Web Port:            {config.web_port}")
        console.print(f"  Secure Web Port:     {config.secure_web_port}")
        console.print(f"  FIPS Mode:           {config.fips_mode}")
        console.print(f"  Firmware URLs:       {len(config.firmware_urls)} configured")
        console.print(f"  Profiles:            {len(config.profiles)} configured")
        console.print(f"  Default Username:    {config.default_username or '(not set)'}")
        console.print(f"  SSH Key Auth:        {'enabled' if config.ssh_key_auth else 'disabled'}")
        console.print()

        action = questionary.select(
            "Settings",
            choices=[
                questionary.Choice("Edit a setting", value="edit"),
                questionary.Choice("Manage Profiles", value="profiles"),
                questionary.Choice("Add firmware URL", value="add_fw"),
                questionary.Choice("Save to disk", value="save"),
                questionary.Choice("Back to main menu", value="back"),
            ],
        ).ask()

        if action is None or action == "back":
            return config
        elif action == "edit":
            config = _edit_setting(config)
        elif action == "profiles":
            config = _flow_manage_profiles(config)
        elif action == "add_fw":
            config = _add_firmware_url(config)
        elif action == "save":
            path = save_config(config)
            console.print(f"[green][OK][/green] Config saved to {path}")

    return config


def _edit_setting(config: Config) -> Config:
    """Edit a single config setting."""
    field = questionary.select(
        "Which setting?",
        choices=[
            questionary.Choice("Timezone", value="timezone"),
            questionary.Choice("NTP Server", value="ntp_server"),
            questionary.Choice("Public Key File", value="pubkey_file"),
            questionary.Choice("Firmware Directory", value="firmware_dir"),
            questionary.Choice("Firmware Server URL", value="firmware_server"),
            questionary.Choice("Web Port", value="web_port"),
            questionary.Choice("Secure Web Port", value="secure_web_port"),
            questionary.Choice("FIPS Mode", value="fips_mode"),
            questionary.Choice("Default Username", value="default_username"),
            questionary.Choice("SSH Key Auth", value="ssh_key_auth"),
            questionary.Choice("Cancel", value="cancel"),
        ],
    ).ask()

    if not field or field == "cancel":
        return config

    if field == "timezone":
        return _pick_timezone(config)

    if field == "ssh_key_auth":
        config.ssh_key_auth = not config.ssh_key_auth
        state = "enabled" if config.ssh_key_auth else "disabled"
        console.print(f"[cyan][INFO][/cyan] SSH key auth {state}")
        return config

    current = getattr(config, field)
    new_value = questionary.text(
        f"{field}:", default=str(current)
    ).ask()

    if new_value is not None:
        if field in ("web_port", "secure_web_port"):
            setattr(config, field, int(new_value))
        else:
            setattr(config, field, new_value)

    return config


def _pick_timezone(config: Config) -> Config:
    """Interactive timezone picker with type-to-filter."""
    choices = [
        questionary.Choice(label, value=tz_id)
        for tz_id, label in timezone_choices()
    ]
    current = config.timezone.zfill(3)
    # Find the matching choice to set as default
    default = None
    for c in choices:
        if c.value == current:
            default = c.value
            break

    result = questionary.select(
        "Select timezone (type to filter):",
        choices=choices,
        default=default,
        use_shortcuts=False,
    ).ask()

    if result is not None:
        config.timezone = result
    return config


def _add_firmware_url(config: Config) -> Config:
    """Add or update a firmware download URL."""
    model = questionary.text("Model name (e.g., CP4, MC4):").ask()
    if not model:
        return config

    url = questionary.text("Firmware download URL:").ask()
    if not url:
        return config

    auth_header = questionary.text(
        "Authorization header (optional, e.g., Bearer TOKEN):",
        default="",
    ).ask()

    from .models import FirmwareSource

    headers = {}
    if auth_header:
        headers["Authorization"] = auth_header

    config.firmware_urls[model.upper()] = FirmwareSource(url=url, headers=headers)
    console.print(f"[green][OK][/green] Firmware URL added for {model.upper()}")
    return config


# --------------------------------------------------------------------------- #
#  Profile management flow
# --------------------------------------------------------------------------- #


def _flow_manage_profiles(config: Config) -> Config:
    """Manage configuration profiles (list, create, edit, delete)."""
    from .models import PROFILE_SETTING_FIELDS

    while True:
        _header("Manage Profiles")

        if config.profiles:
            table = Table(show_header=True, padding=(0, 1))
            table.add_column("Profile", style="cyan")
            table.add_column("Models")
            table.add_column("Overrides")
            table.add_column("Skipped")
            table.add_column("Extra Cmds")

            for name, profile in config.profiles.items():
                models_str = ", ".join(profile.models) if profile.models else "—"
                overrides = sum(
                    1 for f in PROFILE_SETTING_FIELDS
                    if getattr(profile, f) is not None and getattr(profile, f) is not SKIP
                )
                skips = sum(
                    1 for f in PROFILE_SETTING_FIELDS
                    if getattr(profile, f) is SKIP
                )
                extras = len(profile.extra_commands)
                table.add_row(name, models_str, str(overrides), str(skips), str(extras))

            console.print(table)
            console.print()
        else:
            console.print("[dim]No profiles configured.[/dim]")
            console.print()

        action = questionary.select(
            "Profile management",
            choices=[
                questionary.Choice("Create profile", value="create"),
                *(
                    [
                        questionary.Choice("Edit profile", value="edit"),
                        questionary.Choice("Delete profile", value="delete"),
                    ]
                    if config.profiles
                    else []
                ),
                questionary.Choice("Back", value="back"),
            ],
        ).ask()

        if action is None or action == "back":
            return config

        if action == "create":
            config = _create_profile(config)
        elif action == "edit":
            config = _edit_profile(config)
        elif action == "delete":
            config = _delete_profile(config)

    return config


def _create_profile(config: Config) -> Config:
    """Create a new configuration profile."""
    from .models import ExtraCommand

    name = questionary.text("Profile name (e.g., touch-panels):").ask()
    if not name or name in config.profiles:
        if name in config.profiles:
            console.print(f"[red]Profile '{name}' already exists.[/red]")
        return config

    # Model patterns
    models_input = questionary.text(
        "Model patterns (comma-separated globs, e.g., TSW-*,TS-*):",
        default="",
    ).ask()
    models = [m.strip() for m in (models_input or "").split(",") if m.strip()]

    # Settings to skip
    setting_labels = {
        "timezone": "Timezone",
        "ntp_server": "NTP Server",
        "web_port": "Web Port",
        "secure_web_port": "Secure Web Port",
        "fips_mode": "FIPS Mode",
        "user_login_attempts": "User Login Attempts",
        "user_lockout_time": "User Lockout Time",
        "login_attempts": "Console Login Attempts",
        "lockout_time": "Console Lockout Time",
    }

    skip_choices = [
        questionary.Choice(f"{label} (currently: {getattr(config, field)})", value=field)
        for field, label in setting_labels.items()
    ]

    skipped = questionary.checkbox(
        "Select settings to SKIP for this profile (these commands won't be sent):",
        choices=skip_choices,
    ).ask() or []

    # Extra commands
    extra_commands: list[ExtraCommand] = []
    while True:
        add_cmd = questionary.confirm("Add a custom command?", default=False).ask()
        if not add_cmd:
            break
        cmd = questionary.text("Command:").ask()
        if not cmd:
            break
        label = questionary.text("Label (optional):", default="").ask()
        extra_commands.append(ExtraCommand(command=cmd, label=label or ""))

    # Build profile
    kwargs: dict = {"models": models, "extra_commands": extra_commands}
    for field in skipped:
        kwargs[field] = SKIP

    profile = Profile(**kwargs)
    config.profiles[name] = profile
    console.print(f"[green][OK][/green] Profile '{name}' created.")
    console.print("[dim]Use 'Save to disk' in Settings to persist.[/dim]")
    return config


def _edit_profile(config: Config) -> Config:
    """Edit an existing profile."""
    from .models import ExtraCommand, PROFILE_SETTING_FIELDS

    if not config.profiles:
        return config

    name = questionary.select(
        "Select profile to edit:",
        choices=list(config.profiles.keys()) + ["Cancel"],
    ).ask()

    if not name or name == "Cancel":
        return config

    profile = config.profiles[name]

    # Edit model patterns
    current_models = ", ".join(profile.models) if profile.models else ""
    models_input = questionary.text(
        "Model patterns (comma-separated):",
        default=current_models,
    ).ask()
    profile.models = [m.strip() for m in (models_input or "").split(",") if m.strip()]

    # Edit skipped settings
    setting_labels = {
        "timezone": "Timezone",
        "ntp_server": "NTP Server",
        "web_port": "Web Port",
        "secure_web_port": "Secure Web Port",
        "fips_mode": "FIPS Mode",
        "user_login_attempts": "User Login Attempts",
        "user_lockout_time": "User Lockout Time",
        "login_attempts": "Console Login Attempts",
        "lockout_time": "Console Lockout Time",
    }

    current_skipped = [
        f for f in PROFILE_SETTING_FIELDS
        if getattr(profile, f) is SKIP
    ]

    skip_choices = [
        questionary.Choice(
            label,
            value=field,
            checked=field in current_skipped,
        )
        for field, label in setting_labels.items()
    ]

    skipped = questionary.checkbox(
        "Select settings to SKIP:",
        choices=skip_choices,
    ).ask() or []

    # Update skipped fields
    for field in PROFILE_SETTING_FIELDS:
        if field in skipped:
            setattr(profile, field, SKIP)
        elif getattr(profile, field) is SKIP:
            setattr(profile, field, None)  # Un-skip → inherit

    # Edit extra commands
    if profile.extra_commands:
        console.print(f"[bold]Current extra commands ({len(profile.extra_commands)}):[/bold]")
        for ec in profile.extra_commands:
            label = f" ({ec.label})" if ec.label else ""
            console.print(f"  • {ec.command}{label}")

        clear_cmds = questionary.confirm(
            "Clear existing extra commands?", default=False,
        ).ask()
        if clear_cmds:
            profile.extra_commands = []

    while True:
        add_cmd = questionary.confirm("Add a custom command?", default=False).ask()
        if not add_cmd:
            break
        cmd = questionary.text("Command:").ask()
        if not cmd:
            break
        label = questionary.text("Label (optional):", default="").ask()
        profile.extra_commands.append(ExtraCommand(command=cmd, label=label or ""))

    console.print(f"[green][OK][/green] Profile '{name}' updated.")
    console.print("[dim]Use 'Save to disk' in Settings to persist.[/dim]")
    return config


def _delete_profile(config: Config) -> Config:
    """Delete a configuration profile."""
    if not config.profiles:
        return config

    name = questionary.select(
        "Select profile to delete:",
        choices=list(config.profiles.keys()) + ["Cancel"],
    ).ask()

    if not name or name == "Cancel":
        return config

    confirm = questionary.confirm(
        f"Delete profile '{name}'?", default=False,
    ).ask()

    if confirm:
        del config.profiles[name]
        console.print(f"[green][OK][/green] Profile '{name}' deleted.")
        console.print("[dim]Use 'Save to disk' in Settings to persist.[/dim]")

    return config


# --------------------------------------------------------------------------- #
#  Helpers
# --------------------------------------------------------------------------- #


def _prompt_credentials(
    config: Config | None = None,
) -> tuple[str, str] | None:
    """Prompt for admin username and password.

    If config has a default_username, pre-fills it.
    If config.ssh_key_auth is enabled, password is optional (SSH keys tried first).
    """
    default_user = config.default_username if config else ""
    use_keys = config.ssh_key_auth if config else False

    username = questionary.text(
        "Admin username:", default=default_user,
    ).ask()
    if not username:
        return None

    if use_keys:
        use_password = questionary.confirm(
            "Enter password? (No = try SSH key auth only)", default=False,
        ).ask()
        if not use_password:
            return username, ""

    password = questionary.password("Admin password:").ask()
    if not password:
        return None

    confirm = questionary.password("Confirm password:").ask()
    if password != confirm:
        console.print("[red]Passwords do not match.[/red]")
        return None

    return username, password


def _prompt_network_config(device_label: str = "") -> NetworkConfig | None:
    """Prompt for network configuration (DHCP or static IP)."""
    prefix = f"[{device_label}] " if device_label else ""

    mode = questionary.select(
        f"{prefix}IP address mode:",
        choices=[
            questionary.Choice("DHCP (no changes needed)", value="dhcp"),
            questionary.Choice("Static IP", value="static"),
            questionary.Choice("Skip network config", value="skip"),
        ],
    ).ask()

    if mode is None or mode == "skip":
        return None

    new_hostname = questionary.text(
        f"{prefix}Hostname (blank to skip):", default=""
    ).ask()

    if mode == "dhcp":
        return NetworkConfig(mode="dhcp", hostname=new_hostname or "")

    ip = questionary.text(f"{prefix}IP address:").ask()
    if not ip:
        return None

    mask = questionary.text(
        f"{prefix}Subnet mask:", default="255.255.255.0"
    ).ask()
    if not mask:
        return None

    gw = questionary.text(f"{prefix}Default gateway:").ask()
    if not gw:
        return None

    dns_input = questionary.text(
        f"{prefix}DNS servers (comma-separated, or blank to skip):",
        default="",
    ).ask()

    dns_servers = [s.strip() for s in (dns_input or "").split(",") if s.strip()]

    return NetworkConfig(
        mode="static",
        hostname=new_hostname or "",
        ip_address=ip,
        subnet_mask=mask,
        gateway=gw,
        dns_servers=dns_servers,
    )
