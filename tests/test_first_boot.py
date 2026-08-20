"""Tests for first-boot detection (crestron_setup.ssh)."""

from __future__ import annotations

import time

import httpx
import pytest

from crestron_setup import ssh
from crestron_setup.ssh import CrestronFirstBoot


class FakeResponse:
    """Stand-in for an httpx.Response."""

    def __init__(self, url: str, text: str = "", status_code: int = 200):
        self.url = url
        self.text = text
        self.status_code = status_code


@pytest.fixture
def fake_https(monkeypatch):
    """Replace httpx.get with a canned response or exception."""

    def _set(result):
        def _get(*args, **kwargs):
            if isinstance(result, Exception):
                raise result
            return result

        monkeypatch.setattr(ssh.httpx, "get", _get)

    return _set


@pytest.fixture
def all_ports_open(monkeypatch):
    """Pretend every TCP probe succeeds."""
    monkeypatch.setattr(ssh, "_port_open", lambda host, port, timeout=1.0: True)


# ── _check_first_boot_https: tri-state ───────────────────────────────────── #


@pytest.mark.parametrize(
    "response, expected",
    [
        # Redirected to the account-creation page — first boot.
        (FakeResponse("https://h/createUser.html", "<html>create</html>"), True),
        # Not redirected, but the marker is in the body.
        (FakeResponse("https://h/", "go to createUser please"), True),
        # A normal page served — definitively already provisioned.
        (FakeResponse("https://h/login.html", "<html>login</html>"), False),
        (FakeResponse("https://h/", "", 302), False),
        # An error page tells us nothing — inconclusive.
        (FakeResponse("https://h/", "oops", 500), None),
        (FakeResponse("https://h/", "not found", 404), None),
    ],
)
def test_https_check_is_tri_state(fake_https, response, expected):
    fake_https(response)
    assert ssh._check_first_boot_https("h") is expected


@pytest.mark.parametrize(
    "exc",
    [httpx.ConnectTimeout("timed out"), httpx.ConnectError("refused"), OSError("boom")],
)
def test_https_check_returns_none_on_transport_error(fake_https, exc):
    """A failed request must be inconclusive, not a 'provisioned' verdict."""
    fake_https(exc)
    assert ssh._check_first_boot_https("h") is None


# ── check_first_boot: staged probing ─────────────────────────────────────── #


def test_definitive_https_answer_skips_ssh(monkeypatch, fake_https, all_ports_open):
    """A page served without the redirect must not cost an SSH handshake."""
    calls = []
    monkeypatch.setattr(ssh, "_check_first_boot_ssh",
                        lambda *a, **k: calls.append(1) or True)
    fake_https(FakeResponse("https://h/login.html", "login"))

    assert CrestronFirstBoot.check_first_boot("h") is False
    assert not calls, "SSH was attempted after a definitive HTTPS answer"


def test_inconclusive_https_falls_back_to_ssh(monkeypatch, fake_https, all_ports_open):
    calls = []
    monkeypatch.setattr(ssh, "_check_first_boot_ssh",
                        lambda *a, **k: calls.append(1) or True)
    fake_https(FakeResponse("https://h/", "error", 503))

    assert CrestronFirstBoot.check_first_boot("h") is True
    assert calls, "SSH fallback did not run for an inconclusive HTTPS result"


def test_closed_ssh_port_skips_handshake(monkeypatch, fake_https):
    """A closed :22 must short-circuit before paramiko is involved."""
    calls = []
    monkeypatch.setattr(ssh, "_check_first_boot_ssh",
                        lambda *a, **k: calls.append(1) or True)
    monkeypatch.setattr(ssh, "_port_open",
                        lambda host, port, timeout=1.0: port != 22)
    fake_https(FakeResponse("https://h/", "error", 503))

    assert CrestronFirstBoot.check_first_boot("h") is False
    assert not calls


def test_closed_web_port_skips_https(monkeypatch):
    """A closed :443 must short-circuit before the HTTPS request."""
    calls = []
    monkeypatch.setattr(ssh.httpx, "get",
                        lambda *a, **k: calls.append(1) or FakeResponse("https://h/"))
    monkeypatch.setattr(ssh, "_port_open",
                        lambda host, port, timeout=1.0: port != 443)
    monkeypatch.setattr(ssh, "_check_first_boot_ssh", lambda *a, **k: True)

    assert CrestronFirstBoot.check_first_boot("h") is True
    assert not calls


def test_check_respects_its_budget():
    """An unroutable host must not outrun the per-device budget."""
    budget = 3.0
    start = time.monotonic()
    result = CrestronFirstBoot.check_first_boot("198.51.100.42", budget=budget)
    elapsed = time.monotonic() - start

    assert result is False
    # Generous headroom for slow CI runners; the point is that it is bounded
    # and nowhere near the sum of the individual stage timeouts.
    assert elapsed < budget + 3.0, f"took {elapsed:.1f}s for a {budget}s budget"


# ── check_first_boot_batch ───────────────────────────────────────────────── #


def test_batch_runs_concurrently(monkeypatch):
    """32 hosts x 0.2s must finish in far less than the serial 6.4s."""
    monkeypatch.setattr(
        CrestronFirstBoot, "check_first_boot",
        staticmethod(lambda host, budget=1.0: time.sleep(0.2) or host.endswith(".7")),
    )
    hosts = [f"10.0.0.{i}" for i in range(1, 33)]

    start = time.monotonic()
    results = CrestronFirstBoot.check_first_boot_batch(hosts, budget=2.0,
                                                       max_workers=16)
    elapsed = time.monotonic() - start

    assert len(results) == 32
    assert results["10.0.0.7"] is True
    assert results["10.0.0.8"] is False
    assert elapsed < 2.0, f"took {elapsed:.1f}s — checks did not run in parallel"


def test_batch_reports_every_result_through_callback(monkeypatch):
    monkeypatch.setattr(CrestronFirstBoot, "check_first_boot",
                        staticmethod(lambda host, budget=1.0: host == "b"))
    seen: list[tuple[str, bool]] = []

    results = CrestronFirstBoot.check_first_boot_batch(
        ["a", "b", "c"], budget=1.0, on_result=lambda h, v: seen.append((h, v)))

    assert sorted(seen) == [("a", False), ("b", True), ("c", False)]
    assert results == {"a": False, "b": True, "c": False}


def test_batch_deduplicates_hosts_and_ignores_blanks(monkeypatch):
    seen: list[str] = []
    monkeypatch.setattr(
        CrestronFirstBoot, "check_first_boot",
        staticmethod(lambda host, budget=1.0: seen.append(host) or False),
    )

    results = CrestronFirstBoot.check_first_boot_batch(
        ["a", "a", "", "b", None], budget=1.0)  # type: ignore[list-item]

    assert sorted(seen) == ["a", "b"]
    assert results == {"a": False, "b": False}


def test_batch_survives_a_worker_exception(monkeypatch):
    def boom(host, budget=1.0):
        if host == "bad":
            raise RuntimeError("probe blew up")
        return True

    monkeypatch.setattr(CrestronFirstBoot, "check_first_boot", staticmethod(boom))

    results = CrestronFirstBoot.check_first_boot_batch(["bad", "good"], budget=1.0)

    assert results == {"bad": False, "good": True}


def test_batch_is_bounded_by_an_overall_deadline(monkeypatch):
    """A wedged host is reported False instead of hanging the batch."""
    monkeypatch.setattr(
        CrestronFirstBoot, "check_first_boot",
        staticmethod(lambda host, budget=1.0:
                     time.sleep(60) if host == "wedged" else False),
    )

    start = time.monotonic()
    results = CrestronFirstBoot.check_first_boot_batch(
        ["ok", "wedged"], budget=1.0, max_workers=2)
    elapsed = time.monotonic() - start

    assert results == {"ok": False, "wedged": False}
    assert elapsed < 20.0, f"batch took {elapsed:.1f}s — deadline did not fire"


def test_batch_with_no_hosts():
    assert CrestronFirstBoot.check_first_boot_batch([]) == {}


# ── _port_open ───────────────────────────────────────────────────────────── #


def test_port_open_is_false_for_a_closed_port():
    # Nothing listens on this port on the loopback interface.
    assert ssh._port_open("127.0.0.1", 9, timeout=1.0) is False


def test_port_open_is_false_for_a_non_positive_timeout():
    assert ssh._port_open("127.0.0.1", 9, timeout=0) is False


def test_port_open_detects_a_listening_socket():
    import socket

    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    try:
        assert ssh._port_open("127.0.0.1", listener.getsockname()[1], timeout=2.0)
    finally:
        listener.close()
