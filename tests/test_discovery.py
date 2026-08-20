"""Tests for CIP discovery packet construction and response parsing."""

from __future__ import annotations

import pytest

from crestron_setup.discovery import (
    CIP_PORT,
    _device_type_label,
    _parse_response,
    build_discovery_packet,
)


def _cip_response(hostname: str = "MYPROC", model: str = "RMC4",
                  version: str = "2.8006.00284",
                  mac: str = "0011223344ff") -> bytes:
    """Build a synthetic CIP discovery response like a processor sends."""
    return (
        b"\x15\x00" + b"\x00" * 8
        + hostname.encode() + b"\x00"
        + f"{model} [v{version} (Nov 14 2024), #01234567] @E-{mac}".encode()
        + b"\x00"
    )


# ── build_discovery_packet ───────────────────────────────────────────────── #


def test_discovery_packet_is_the_expected_length():
    assert len(build_discovery_packet()) == 266


def test_discovery_packet_has_the_cip_header():
    assert build_discovery_packet().startswith(b"\x14\x00\x00\x00\x01\x04\x00\x03")


def test_discovery_packet_carries_the_hostname_then_only_padding():
    import socket

    packet = build_discovery_packet()
    hostname = socket.gethostname().encode("ascii", errors="ignore")

    assert packet[10:10 + len(hostname)] == hostname
    # Everything after the hostname is null padding.
    assert set(packet[10 + len(hostname):]) == {0}


def test_cip_port_is_unchanged():
    # Devices only answer on 41794; a change here breaks discovery outright.
    assert CIP_PORT == 41794


# ── _parse_response ──────────────────────────────────────────────────────── #


def test_parses_a_well_formed_response():
    device = _parse_response(_cip_response(), "192.168.1.50")

    assert device is not None
    assert device.ip == "192.168.1.50"
    assert device.hostname == "MYPROC"
    assert device.model == "RMC4"
    assert device.firmware_version == "2.8006.00284"
    assert device.mac == "00:11:22:33:44:ff"
    assert device.is_first_boot is False


def test_parses_a_hyphenated_model():
    device = _parse_response(_cip_response(model="TSW-1070"), "10.0.0.5")

    assert device is not None
    assert device.model == "TSW-1070"


@pytest.mark.parametrize("data", [
    b"",                                  # empty datagram
    b"\x14\x00" + b"\x00" * 20,           # our own outbound broadcast
    b"\x16\x00" + b"\x00" * 20,           # some other CIP message
])
def test_rejects_non_discovery_responses(data):
    assert _parse_response(data, "10.0.0.1") is None


def test_missing_fields_are_empty_rather_than_fatal():
    device = _parse_response(b"\x15\x00" + b"\x00" * 20, "10.0.0.1")

    assert device is not None
    assert device.ip == "10.0.0.1"
    assert device.hostname == ""
    assert device.model == ""
    assert device.firmware_version == ""
    assert device.mac == ""


# ── _device_type_label ───────────────────────────────────────────────────── #


@pytest.mark.parametrize("model, expected", [
    ("UC-ENGINE", "UC Engine"),
    ("UC-BX-30-Z", "UC Engine"),
    ("TSW-1070", "Touchpanel"),
    ("TS-1070", "Touchpanel"),
    ("TST-1080", "Touchpanel"),
    ("RMC4", "Processor"),
    ("CP4", "Processor"),
    ("MC4", "Processor"),
    ("", "Processor"),
])
def test_device_type_label(model, expected):
    assert _device_type_label(model) == expected
