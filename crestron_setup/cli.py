"""Interactive CLI console for Crestron processor provisioning."""

from __future__ import annotations

import os
import select
import sys
import time
from concurrent.futures import Future, ThreadPoolExecutor

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
from rich.table import Table
from rich.text import Text

from .config import load_config, save_config
from .discovery import discover_devices, print_device_table
from .firmware import cache_info, clear_cache, download_firmware, download_firmware_quiet, find_local_firmware
from .models import Config, Device, NetworkConfig, Profile, SKIP
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
) -> str | None:
    """Prompt the user to select a configuration profile.

    Returns profile name or None for default (no profile).
    """
    if not config.profiles:
        return None

    choices = []
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
            questionary.Choice("Upload Program", value="program"),
            questionary.Choice("Firmware Audit", value="fw_audit"),
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
        elif choice == "program":
            config = _flow_upload_program(config)
        elif choice == "restore":
            _flow_restore()
        elif choice == "fw_audit":
            _flow_firmware_audit(config)
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

    # Check first-boot state for each device
    console.print("Checking first-boot state...")
    for dev in devices:
        dev.is_first_boot = CrestronFirstBoot.check_first_boot(dev.ip)

    _header("Discover Devices")
    print_device_table(devices, console)
    console.print()

    # Pick action first
    action = questionary.select(
        "What do you want to do?",
        choices=[
            questionary.Choice("Provision", value="provision"),
            questionary.Choice("Provision (Dry Run)", value="dry_run"),
            questionary.Choice("Upload Program", value="program"),
            questionary.Choice("Restore & Erase", value="restore"),
            questionary.Choice("Back to Main Menu", value="back"),
        ],
    ).ask()

    if action is None or action == "back":
        return config

    # Select devices
    device_choices = [
        questionary.Choice(
            f"{dev.ip:<17} {dev.hostname:<20} {dev.model:<12} "
            f"{'[FIRST BOOT]' if dev.is_first_boot else ''}",
            value=i,
        )
        for i, dev in enumerate(devices)
    ]

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
    creds = _prompt_credentials()
    if not creds:
        return config
    username, password = creds

    # Gather action-specific inputs before starting parallel execution
    program_path: str = ""
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

    # Profile selection for provision actions
    profile_name: str | None = None
    if action in ("provision", "dry_run") and config.profiles:
        # Auto-suggest based on device models
        models = {d.model for d in selected_devices if d.model}
        suggested = None
        for m in models:
            suggested = match_profile(m, config)
            if suggested:
                break
        profile_name = _prompt_profile_selection(config, suggested)

    # ── Single device: run normally with full display ──────────────────
    if len(selected_devices) == 1:
        dev = selected_devices[0]
        if action == "provision":
            provision_device(dev, username, password, config, console,
                             profile_name=profile_name)
        elif action == "dry_run":
            provision_device(dev, username, password, config, console,
                             dry_run=True, profile_name=profile_name)
        elif action == "program":
            host = dev.ip or dev.hostname
            upload_program(host, username, password, program_path, slot, console)
        elif action == "restore":
            restore_device(dev, username, password, console)
        _pause()
        return config

    # ── Multiple devices: run in parallel with combined display ────────
    device_results = _run_parallel(
        action, selected_devices, username, password,
        config, program_path, slot, profile_name=profile_name,
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
        else:  # restore
            from .provisioning import RESTORE_PHASE_NAMES
            tracker = _StepTracker(label, list(RESTORE_PHASE_NAMES))
        device_results.append(DeviceResult(
            device_label=label, action=action, success=False, tracker=tracker,
        ))

    display = _ParallelDisplay(device_results)

    def _worker(dev: Device, dr: DeviceResult) -> None:
        """Thread worker — runs action headlessly using dr.tracker for live updates."""
        host = dev.ip or dev.hostname
        if action == "provision":
            result = provision_device(
                dev, username, password, config, console,
                headless=True, tracker=dr.tracker,
                profile_name=profile_name,
            )
            dr.success, _, dr.results = result  # type: ignore[misc]
        elif action == "dry_run":
            result = provision_device(
                dev, username, password, config, console,
                headless=True, tracker=dr.tracker, dry_run=True,
                profile_name=profile_name,
            )
            dr.success, _, dr.results = result  # type: ignore[misc]
        elif action == "program":
            result = upload_program(
                host, username, password, program_path, slot, console,
                headless=True, tracker=dr.tracker,
            )
            dr.success = result[0]  # type: ignore[index]
        elif action == "restore":
            result = restore_device(
                dev, username, password, console,
                headless=True, tracker=dr.tracker,
            )
            dr.success = result[0]  # type: ignore[index]

    _clear()
    with Live(display, console=console, refresh_per_second=8) as live:
        with ThreadPoolExecutor(max_workers=len(devices)) as pool:
            futures = [
                pool.submit(_worker, dev, dr)
                for dev, dr in zip(devices, device_results)
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
            _show_dry_run_results(
                console, dr.tracker, dr.results, dr.success, config,
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

    creds = _prompt_credentials()
    if not creds:
        return
    username, password = creds

    device = Device(ip=host)

    # Quick first-boot check
    console.print("Checking first-boot state...")
    device.is_first_boot = CrestronFirstBoot.check_first_boot(host)
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
#  Upload Program flow
# --------------------------------------------------------------------------- #


def _flow_upload_program(config: Config) -> Config:
    """Upload a program file to a processor and load it."""
    _header("Upload Program")

    host = questionary.text("Processor hostname or IP:").ask()
    if not host:
        return config

    username = questionary.text("Admin username:").ask()
    if not username:
        return config

    password = questionary.password("Admin password:").ask()
    if not password:
        return config

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

    # Remember the program file for next time
    config.last_program_file = program_path
    save_config(config)

    upload_program(host, username, password, program_path, slot, console)
    _pause()
    return config


# --------------------------------------------------------------------------- #
#  Restore & Erase flow
# --------------------------------------------------------------------------- #


def _flow_restore() -> None:
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
    restore_device(device, username, password, console)
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
        download_firmware_quiet,
        find_local_firmware,
        query_firmware_server,
        version_compare,
    )
    from .ssh import CrestronSSH

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

    # Need credentials to read full PUF version via VER -V
    # Check for first-boot devices first
    console.print("Checking first-boot state…")
    first_boot_devices: list[Device] = []
    ready_devices: list[Device] = []
    for dev in devices:
        dev.is_first_boot = CrestronFirstBoot.check_first_boot(dev.ip)
        if dev.is_first_boot:
            first_boot_devices.append(dev)
        else:
            ready_devices.append(dev)

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
        creds = _prompt_credentials()
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
                with CrestronSSH(host, username, password) as ssh:
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

        # 1. Check firmware server API for version (no download needed)
        if config.firmware_server:
            server_info = query_firmware_server(fw_model, config.firmware_server)
            if server_info:
                fw_version = server_info.version

        # 2. Check local files
        if not fw_version:
            fw_path, fw_version = find_local_firmware(fw_model, config)

        # 3. Try downloading quietly
        if not fw_version:
            fw_path = download_firmware_quiet(fw_model, config)
            if fw_path:
                fw_version, _ = _parse_puf_metadata(fw_path)

        if not fw_version:
            result.status = "unknown"
            result.detail = "No firmware available"
            return result

        result.available_version = fw_version
        result.available_path = fw_path.name if fw_path else "(server)"

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
    table.add_column("Status", min_width=18)

    for r in results:
        host = r.device.ip or r.device.hostname
        model = r.device.model or "—"
        current = r.current_version or "—"

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

        table.add_row(host, model, current, available, status)

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
#  Settings flow
# --------------------------------------------------------------------------- #


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
            questionary.Choice("Cancel", value="cancel"),
        ],
    ).ask()

    if not field or field == "cancel":
        return config

    if field == "timezone":
        return _pick_timezone(config)

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
    from .models import ExtraCommand, PROFILE_SETTING_FIELDS

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
    from .models import ExtraCommand, PROFILE_SETTING_FIELDS

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


def _prompt_credentials() -> tuple[str, str] | None:
    """Prompt for admin username and password."""
    username = questionary.text("Admin username:").ask()
    if not username:
        return None

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
