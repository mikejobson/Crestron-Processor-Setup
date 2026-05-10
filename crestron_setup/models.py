"""Data models for Crestron processor provisioning."""

from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Any

# Sentinel indicating a setting should be skipped (not sent to the device).
# In YAML this is represented as ``false``.
SKIP = object()


@dataclass
class NetworkConfig:
    """IP configuration for a device's primary NIC."""

    mode: str = "dhcp"  # "dhcp" or "static"
    hostname: str = ""
    ip_address: str = ""
    subnet_mask: str = "255.255.255.0"
    gateway: str = ""
    dns_servers: list[str] = field(default_factory=list)


@dataclass
class Device:
    """A discovered or manually-specified Crestron processor."""

    ip: str
    hostname: str = ""
    model: str = ""
    firmware_version: str = ""
    mac: str = ""
    is_first_boot: bool = False
    network: NetworkConfig | None = None

    @property
    def display_name(self) -> str:
        parts = [self.hostname or self.ip]
        if self.model:
            parts.append(f"({self.model})")
        return " ".join(parts)


@dataclass
class FirmwareSource:
    """Download location for a model's firmware."""

    url: str
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class ExtraCommand:
    """A custom CLI command to run during provisioning."""

    command: str
    label: str = ""


@dataclass
class Profile:
    """A named configuration profile that overrides default settings.

    Fields set to ``None`` inherit from the default config.
    Fields set to the ``SKIP`` sentinel are excluded (command not sent).
    Fields set to a value override the default.
    """

    # Model glob patterns for auto-matching (e.g. ["TSW-*", "TS-*"])
    models: list[str] = field(default_factory=list)
    # Custom commands appended after standard phase-3 configuration
    extra_commands: list[ExtraCommand] = field(default_factory=list)

    # Overridable settings — None means inherit from default
    timezone: str | None | object = None
    ntp_server: str | None | object = None
    pubkey_file: str | None | object = None
    web_port: int | None | object = None
    secure_web_port: int | None | object = None
    user_login_attempts: int | None | object = None
    user_lockout_time: str | None | object = None
    login_attempts: int | None | object = None
    lockout_time: str | None | object = None
    fips_mode: str | None | object = None

    def matches_model(self, model: str) -> bool:
        """Check if this profile's model patterns match a device model."""
        if not self.models:
            return False
        return any(fnmatch(model.upper(), p.upper()) for p in self.models)


# Fields on Profile that correspond to Config settings
PROFILE_SETTING_FIELDS = [
    "timezone", "ntp_server", "pubkey_file", "web_port", "secure_web_port",
    "user_login_attempts", "user_lockout_time", "login_attempts",
    "lockout_time", "fips_mode",
]


@dataclass
class ResolvedProfile:
    """The result of merging a Profile with the default Config.

    Provides effective values for each setting and tracks which are skipped.
    """

    name: str
    config: Config
    skipped: set[str]
    extra_commands: list[ExtraCommand]


def resolve_profile(profile_name: str | None, config: Config) -> ResolvedProfile:
    """Merge a named profile with default config values.

    Returns a ResolvedProfile with effective config, skipped fields, and
    extra commands.  If profile_name is None or not found, returns the
    default config with no skips.
    """
    skipped: set[str] = set()
    extras: list[ExtraCommand] = []

    if not profile_name or profile_name not in config.profiles:
        return ResolvedProfile(
            name=profile_name or "default",
            config=config,
            skipped=skipped,
            extra_commands=extras,
        )

    profile = config.profiles[profile_name]
    extras = list(profile.extra_commands)

    # Build a modified copy of the config with profile overrides
    overrides: dict[str, Any] = {}
    for fld in PROFILE_SETTING_FIELDS:
        val = getattr(profile, fld)
        if val is SKIP:
            skipped.add(fld)
        elif val is not None:
            overrides[fld] = val

    # Create a new Config with overrides applied
    effective = Config(
        timezone=overrides.get("timezone", config.timezone),
        ntp_server=overrides.get("ntp_server", config.ntp_server),
        pubkey_file=overrides.get("pubkey_file", config.pubkey_file),
        firmware_dir=config.firmware_dir,
        web_port=overrides.get("web_port", config.web_port),
        secure_web_port=overrides.get("secure_web_port", config.secure_web_port),
        user_login_attempts=overrides.get(
            "user_login_attempts", config.user_login_attempts
        ),
        user_lockout_time=overrides.get(
            "user_lockout_time", config.user_lockout_time
        ),
        login_attempts=overrides.get("login_attempts", config.login_attempts),
        lockout_time=overrides.get("lockout_time", config.lockout_time),
        fips_mode=overrides.get("fips_mode", config.fips_mode),
        last_program_file=config.last_program_file,
        firmware_urls=config.firmware_urls,
        firmware_server=config.firmware_server,
        discovery_timeout=config.discovery_timeout,
        discovery_broadcast_count=config.discovery_broadcast_count,
        profiles=config.profiles,
    )

    return ResolvedProfile(
        name=profile_name,
        config=effective,
        skipped=skipped,
        extra_commands=extras,
    )


@dataclass
class Config:
    """Application configuration loaded from YAML."""

    timezone: str = "33"
    ntp_server: str = "pool.ntp.org"
    pubkey_file: str = "~/.ssh/id_rsa.pub"
    firmware_dir: str = "~/Downloads"
    web_port: int = 8080
    secure_web_port: int = 8443
    user_login_attempts: int = 5
    user_lockout_time: str = "1m"
    login_attempts: int = 20
    lockout_time: str = "5m"
    fips_mode: str = "OFF"
    last_program_file: str = ""
    firmware_urls: dict[str, FirmwareSource] = field(default_factory=dict)
    firmware_server: str = ""
    discovery_timeout: int = 5
    discovery_broadcast_count: int = 3
    profiles: dict[str, Profile] = field(default_factory=dict)
