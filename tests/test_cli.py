"""Tests for the CLI's first-boot batch wiring."""

from __future__ import annotations

import time

from crestron_setup import cli, ssh
from crestron_setup.models import Config, Device


def _stub_check(monkeypatch, fn):
    monkeypatch.setattr(ssh.CrestronFirstBoot, "check_first_boot", staticmethod(fn))


def test_states_are_written_back_onto_the_devices(monkeypatch):
    _stub_check(monkeypatch, lambda host, budget=10.0: host == "10.0.0.2")
    devices = [Device(ip="10.0.0.1"), Device(ip="10.0.0.2"), Device(ip="10.0.0.3")]

    cli._check_first_boot_states(devices, Config())

    assert [d.is_first_boot for d in devices] == [False, True, False]


def test_devices_are_checked_in_parallel(monkeypatch):
    _stub_check(monkeypatch, lambda host, budget=10.0: time.sleep(0.2) or False)
    devices = [Device(ip=f"10.0.0.{i}") for i in range(1, 17)]

    start = time.monotonic()
    cli._check_first_boot_states(devices, Config(discovery_probe_workers=16))
    elapsed = time.monotonic() - start

    assert elapsed < 1.5, f"took {elapsed:.1f}s — serial would be ~3.2s"


def test_config_budget_and_workers_are_passed_through(monkeypatch):
    seen: dict = {}

    def _batch(hosts, budget=None, max_workers=None, on_result=None):
        seen.update(hosts=list(hosts), budget=budget, max_workers=max_workers)
        return {h: False for h in hosts}

    monkeypatch.setattr(ssh.CrestronFirstBoot, "check_first_boot_batch",
                        staticmethod(_batch))
    cfg = Config(discovery_probe_timeout=12.5, discovery_probe_workers=4)

    cli._check_first_boot_states([Device(ip="10.0.0.1")], cfg)

    assert seen["budget"] == 12.5
    assert seen["max_workers"] == 4
    assert seen["hosts"] == ["10.0.0.1"]


def test_a_host_is_only_probed_once_for_duplicate_devices(monkeypatch):
    probed: list[str] = []
    _stub_check(monkeypatch,
                lambda host, budget=10.0: probed.append(host) or True)
    devices = [Device(ip="10.0.0.1"), Device(ip="10.0.0.1", hostname="dupe")]

    cli._check_first_boot_states(devices, Config())

    assert probed == ["10.0.0.1"]
    # …but both device records still get the result.
    assert all(d.is_first_boot for d in devices)


def test_hostname_is_used_when_no_ip_is_known(monkeypatch):
    probed: list[str] = []
    _stub_check(monkeypatch,
                lambda host, budget=10.0: probed.append(host) or False)

    cli._check_first_boot_states([Device(ip="", hostname="proc.local")], Config())

    assert probed == ["proc.local"]


def test_addressless_devices_are_skipped(monkeypatch):
    probed: list[str] = []
    _stub_check(monkeypatch,
                lambda host, budget=10.0: probed.append(host) or True)
    devices = [Device(ip=""), Device(ip="10.0.0.1")]

    cli._check_first_boot_states(devices, Config())

    assert probed == ["10.0.0.1"]
    assert devices[0].is_first_boot is False


def test_no_devices_is_a_no_op():
    cli._check_first_boot_states([], Config())
