"""Interactive CLI console for Crestron processor provisioning."""

from __future__ import annotations

import os
import sys

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .config import load_config, save_config
from .discovery import discover_devices, print_device_table
from .firmware import download_firmware, find_local_firmware
from .models import Config, Device, NetworkConfig
from .provisioning import provision_device, restore_device, upload_program
from .ssh import CrestronFirstBoot
from .timezones import timezone_choices, timezone_label
from . import __version__

console = Console()


def _clear() -> None:
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


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
    config = load_config()

    while True:
        _clear()
        _banner()

        choice = questionary.select(
            "Main Menu",
            choices=[
                questionary.Choice("Discover Devices", value="discover"),
                questionary.Choice("Setup Device (manual IP)", value="setup"),
                questionary.Choice("Upload Program", value="program"),
                questionary.Choice("Restore & Erase Device", value="restore"),
                questionary.Choice("Download Firmware", value="firmware"),
                questionary.Choice("Settings", value="settings"),
                questionary.Choice("Exit", value="exit"),
            ],
        ).ask()

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
        elif choice == "firmware":
            _flow_firmware(config)
        elif choice == "settings":
            config = _flow_settings(config)


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

    # ── Provision ──────────────────────────────────────────────────────
    if action == "provision":
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

        for dev in selected_devices:
            provision_device(dev, username, password, config, console)

    # ── Upload Program ─────────────────────────────────────────────────
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

        for dev in selected_devices:
            host = dev.ip or dev.hostname
            upload_program(host, username, password, program_path, slot, console)

    # ── Restore & Erase ────────────────────────────────────────────────
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

        for dev in selected_devices:
            restore_device(dev, username, password, console)

    _pause()
    return config


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

    provision_device(device, username, password, config, console)
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
        console.print(f"  Web Port:            {config.web_port}")
        console.print(f"  Secure Web Port:     {config.secure_web_port}")
        console.print(f"  FIPS Mode:           {config.fips_mode}")
        console.print(f"  Firmware URLs:       {len(config.firmware_urls)} configured")
        console.print()

        action = questionary.select(
            "Settings",
            choices=[
                questionary.Choice("Edit a setting", value="edit"),
                questionary.Choice("Add firmware URL", value="add_fw"),
                questionary.Choice("Save to disk", value="save"),
                questionary.Choice("Back to main menu", value="back"),
            ],
        ).ask()

        if action is None or action == "back":
            return config
        elif action == "edit":
            config = _edit_setting(config)
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
