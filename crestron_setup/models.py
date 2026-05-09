"""Data models for Crestron processor provisioning."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Device:
    """A discovered or manually-specified Crestron processor."""

    ip: str
    hostname: str = ""
    model: str = ""
    firmware_version: str = ""
    mac: str = ""
    is_first_boot: bool = False

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
class Config:
    """Application configuration loaded from YAML."""

    timezone: str = "33"
    ntp_server: str = "pool.ntp.org"
    pubkey_file: str = "~/.ssh/id_rsa.pub"
    firmware_dir: str = "~/Sync/Crestron Firmware"
    web_port: int = 8080
    secure_web_port: int = 8443
    user_login_attempts: int = 5
    user_lockout_time: str = "1m"
    login_attempts: int = 20
    lockout_time: str = "5m"
    fips_mode: str = "OFF"
    firmware_urls: dict[str, FirmwareSource] = field(default_factory=dict)
    discovery_timeout: int = 5
    discovery_broadcast_count: int = 3
