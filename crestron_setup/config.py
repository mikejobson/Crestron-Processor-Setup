"""Configuration loading and management."""

from __future__ import annotations

import os
import platform
from pathlib import Path

import yaml

from .models import Config, FirmwareSource

APP_NAME = "crestron-setup"


def _config_dir() -> Path:
    """Return the platform-appropriate config directory."""
    if platform.system() == "Windows":
        base = os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
        return Path(base) / APP_NAME
    return Path.home() / ".config" / APP_NAME


def _config_path() -> Path:
    return _config_dir() / "config.yaml"


def _parse_firmware_urls(raw: dict | None) -> dict[str, FirmwareSource]:
    """Parse firmware_urls section from YAML into FirmwareSource objects."""
    if not raw:
        return {}
    result: dict[str, FirmwareSource] = {}
    for model, value in raw.items():
        if isinstance(value, str):
            result[model.upper()] = FirmwareSource(url=value)
        elif isinstance(value, dict):
            result[model.upper()] = FirmwareSource(
                url=value.get("url", ""),
                headers=value.get("headers", {}),
            )
    return result


def load_config() -> Config:
    """Load config from YAML, falling back to defaults for missing keys."""
    # Check local config first, then platform config dir
    local = Path("config.yaml")
    path = local if local.exists() else _config_path()

    data: dict = {}
    if path.exists():
        with open(path) as f:
            data = yaml.safe_load(f) or {}

    discovery = data.get("discovery", {})

    return Config(
        timezone=str(data.get("timezone", "33")),
        ntp_server=data.get("ntp_server", "pool.ntp.org"),
        pubkey_file=data.get("pubkey_file", "~/.ssh/id_rsa.pub"),
        firmware_dir=data.get("firmware_dir", "~/Sync/Crestron Firmware"),
        web_port=int(data.get("web_port", 8080)),
        secure_web_port=int(data.get("secure_web_port", 8443)),
        user_login_attempts=int(data.get("user_login_attempts", 5)),
        user_lockout_time=str(data.get("user_lockout_time", "1m")),
        login_attempts=int(data.get("login_attempts", 20)),
        lockout_time=str(data.get("lockout_time", "5m")),
        fips_mode=str(data.get("fips_mode", "OFF")).upper(),
        firmware_urls=_parse_firmware_urls(data.get("firmware_urls")),
        discovery_timeout=int(discovery.get("timeout", 5)),
        discovery_broadcast_count=int(discovery.get("broadcast_count", 3)),
    )


def save_config(config: Config) -> Path:
    """Save current config to the platform config directory."""
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    # Build firmware_urls for YAML
    fw_urls: dict = {}
    for model, src in config.firmware_urls.items():
        if src.headers:
            fw_urls[model] = {"url": src.url, "headers": src.headers}
        else:
            fw_urls[model] = src.url

    data = {
        "timezone": config.timezone,
        "ntp_server": config.ntp_server,
        "pubkey_file": config.pubkey_file,
        "firmware_dir": config.firmware_dir,
        "web_port": config.web_port,
        "secure_web_port": config.secure_web_port,
        "user_login_attempts": config.user_login_attempts,
        "user_lockout_time": config.user_lockout_time,
        "login_attempts": config.login_attempts,
        "lockout_time": config.lockout_time,
        "fips_mode": config.fips_mode,
        "firmware_urls": fw_urls,
        "discovery": {
            "timeout": config.discovery_timeout,
            "broadcast_count": config.discovery_broadcast_count,
        },
    }

    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    return path
