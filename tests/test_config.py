"""Tests for config loading, saving, and the shipped example file."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from crestron_setup import config as config_module
from crestron_setup.config import load_config, save_config
from crestron_setup.models import Config, Profile, SKIP, resolve_profile

EXAMPLE = Path(__file__).resolve().parent.parent / "config.example.yaml"


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    """Run load/save against a temp directory, not the developer's real config."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config_module, "_config_path",
                        lambda: tmp_path / "saved" / "config.yaml")
    return tmp_path


def _write(tmp_path: Path, data: dict) -> None:
    (tmp_path / "config.yaml").write_text(yaml.dump(data))


# ── defaults ─────────────────────────────────────────────────────────────── #


def test_defaults_when_no_config_file(isolated_config):
    cfg = load_config()

    assert cfg.timezone == "33"
    assert cfg.ntp_server == "pool.ntp.org"
    assert cfg.discovery_timeout == 5
    assert cfg.discovery_broadcast_count == 3
    assert cfg.discovery_probe_timeout == 10.0
    assert cfg.discovery_probe_workers == 16


def test_config_dataclass_defaults_match_loader_defaults(isolated_config):
    """A missing key must land on the same value as the dataclass default."""
    loaded, default = load_config(), Config()

    for field in ("discovery_timeout", "discovery_broadcast_count",
                  "discovery_probe_timeout", "discovery_probe_workers"):
        assert getattr(loaded, field) == getattr(default, field), field


# ── discovery / probe settings ───────────────────────────────────────────── #


def test_discovery_probe_settings_are_read(isolated_config):
    _write(isolated_config, {"discovery": {"timeout": 8, "broadcast_count": 5,
                                           "probe_timeout": 15,
                                           "probe_workers": 32}})
    cfg = load_config()

    assert cfg.discovery_timeout == 8
    assert cfg.discovery_broadcast_count == 5
    assert cfg.discovery_probe_timeout == 15.0
    assert cfg.discovery_probe_workers == 32


@pytest.mark.parametrize("given, expected", [(0, 2.0), (0.5, 2.0), (-5, 2.0),
                                             (2, 2.0), (30, 30.0)])
def test_probe_timeout_is_floored(isolated_config, given, expected):
    """Too small a budget would make every device read as 'not first boot'."""
    _write(isolated_config, {"discovery": {"probe_timeout": given}})

    assert load_config().discovery_probe_timeout == expected


@pytest.mark.parametrize("given, expected", [(0, 1), (-3, 1), (1, 1), (64, 64)])
def test_probe_workers_is_floored(isolated_config, given, expected):
    _write(isolated_config, {"discovery": {"probe_workers": given}})

    assert load_config().discovery_probe_workers == expected


# ── round trip ───────────────────────────────────────────────────────────── #


def test_save_then_load_preserves_probe_settings(isolated_config):
    cfg = load_config()
    cfg.discovery_probe_timeout = 20.0
    cfg.discovery_probe_workers = 48

    saved = save_config(cfg)
    (isolated_config / "config.yaml").write_text(saved.read_text())
    reloaded = load_config()

    assert reloaded.discovery_probe_timeout == 20.0
    assert reloaded.discovery_probe_workers == 48


def test_saved_yaml_nests_probe_settings_under_discovery(isolated_config):
    data = yaml.safe_load(save_config(load_config()).read_text())

    assert set(data["discovery"]) == {"timeout", "broadcast_count",
                                      "probe_timeout", "probe_workers"}


# ── profiles ─────────────────────────────────────────────────────────────── #


def test_resolved_profile_carries_probe_settings_through():
    """resolve_profile() rebuilds Config by hand — easy to drop a field."""
    cfg = Config(discovery_probe_timeout=25.0, discovery_probe_workers=7,
                 profiles={"p": Profile(timezone="1")})

    effective = resolve_profile("p", cfg).config

    assert effective.timezone == "1"
    assert effective.discovery_probe_timeout == 25.0
    assert effective.discovery_probe_workers == 7


def test_profile_parsing_and_skip_sentinel(isolated_config):
    _write(isolated_config, {"profiles": {"panels": {
        "models": ["TSW-*", "TS-*"],
        "timezone": "5",
        "fips_mode": False,
        "extra_commands": ["REBOOT", {"command": "VER", "label": "Version"}],
    }}})
    profile = load_config().profiles["panels"]

    assert profile.matches_model("TSW-1070")
    assert not profile.matches_model("RMC4")
    assert profile.timezone == "5"
    assert profile.fips_mode is SKIP
    assert [c.command for c in profile.extra_commands] == ["REBOOT", "VER"]
    assert profile.extra_commands[1].label == "Version"


# ── the shipped example ──────────────────────────────────────────────────── #


def test_example_config_is_valid_yaml():
    assert isinstance(yaml.safe_load(EXAMPLE.read_text()), dict)


def test_example_config_loads_without_falling_back_to_defaults(isolated_config):
    """Every key in config.example.yaml must actually be honoured."""
    (isolated_config / "config.yaml").write_text(EXAMPLE.read_text())
    example = yaml.safe_load(EXAMPLE.read_text())
    cfg = load_config()

    discovery = example.get("discovery", {})
    assert cfg.discovery_timeout == discovery["timeout"]
    assert cfg.discovery_broadcast_count == discovery["broadcast_count"]
    assert cfg.discovery_probe_timeout == float(discovery["probe_timeout"])
    assert cfg.discovery_probe_workers == discovery["probe_workers"]
    assert cfg.timezone == str(example["timezone"])
    assert cfg.ntp_server == example["ntp_server"]
