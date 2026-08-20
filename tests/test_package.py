"""Import and packaging smoke tests — the checks a version matrix earns."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

MODULES = [
    "crestron_setup",
    "crestron_setup.cli",
    "crestron_setup.config",
    "crestron_setup.ctp",
    "crestron_setup.discovery",
    "crestron_setup.firmware",
    "crestron_setup.models",
    "crestron_setup.provisioning",
    "crestron_setup.ssh",
    "crestron_setup.timezones",
    "crestron_setup.updater",
]


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name):
    assert importlib.import_module(name) is not None


def test_entry_point_is_callable():
    from crestron_setup.cli import main

    assert callable(main)


def test_version_is_exposed():
    import crestron_setup

    assert isinstance(crestron_setup.__version__, str)
    assert crestron_setup.__version__


def test_welcome_animation_ships_with_the_package():
    """This file is declared as package-data and bundled by PyInstaller."""
    import crestron_setup

    animation = Path(crestron_setup.__file__).parent / "welcome_animation.json"
    assert animation.is_file()
    assert animation.stat().st_size > 0


def test_timezone_table_is_usable():
    from crestron_setup.timezones import timezone_choices, timezone_label

    assert timezone_label("33")
    assert len(timezone_choices()) > 1
