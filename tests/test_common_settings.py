"""Tests for the bulk common-settings push."""

from __future__ import annotations

from datetime import datetime

import pytest

from crestron_setup import cli
from crestron_setup.models import CommonSettings, Config, Device
from crestron_setup.provisioning import (
    apply_common_settings,
    build_common_setting_commands,
    parse_dns_servers,
    plan_dns_changes,
)

# Settings that identify a single device and must never be sent by this flow.
PER_DEVICE_COMMANDS = ("IPADDRESS", "IPMASK", "DEFROUTER", "HOSTNAME", "DHCP")


# ── parse_dns_servers ────────────────────────────────────────────────────── #

WINDOWS_STYLE = """
Ethernet adapter LAN:
        DHCP Enabled. . . . . . . . . . . : No
        IP Address. . . . . . . . . . . . : 192.168.1.50
        Subnet Mask . . . . . . . . . . . : 255.255.255.0
        Default Gateway . . . . . . . . . : 192.168.1.1
        DNS Servers . . . . . . . . . . . : 10.0.0.1
                                            10.0.0.2
"""

CRESTRON_STYLE = """
Ethernet
   DHCP.............................. OFF
   IP Address........................ 192.168.1.50
   Subnet Mask....................... 255.255.255.0
   Default Gateway................... 192.168.1.1
   DNS Server........................ 8.8.8.8
   Domain............................ example.local
"""


@pytest.mark.parametrize(
    "output, expected",
    [
        (WINDOWS_STYLE, ["10.0.0.1", "10.0.0.2"]),
        (CRESTRON_STYLE, ["8.8.8.8"]),
        # Static and dynamic entries both count.
        ("   Static DNS Server....... 10.1.1.1\n"
         "   Dynamic DNS Server...... 10.1.1.2\n", ["10.1.1.1", "10.1.1.2"]),
        # Repeated server reported twice is returned once.
        ("   DNS Server..... 9.9.9.9\n   DNS Server 2..... 9.9.9.9\n", ["9.9.9.9"]),
        # Unset placeholders are not servers.
        ("   DNS Server........ 0.0.0.0\n", []),
        # No DNS line at all.
        ("   IP Address..... 192.168.1.50\n   Default Gateway..... 1.2.3.4\n", []),
        # An unrecognised layout must yield nothing rather than a wrong answer.
        ("some completely different output\nwith no fields\n", []),
        ("", []),
    ],
)
def test_parse_dns_servers(output, expected):
    assert parse_dns_servers(output) == expected


def test_parse_dns_does_not_mistake_gateway_or_ip_for_dns():
    """The addresses on other labelled lines must not leak into the result."""
    servers = parse_dns_servers(CRESTRON_STYLE)
    assert "192.168.1.1" not in servers   # gateway
    assert "192.168.1.50" not in servers  # the device itself
    assert "255.255.255.0" not in servers  # mask


def test_parse_dns_rejects_out_of_range_octets():
    assert parse_dns_servers("   DNS Server..... 999.1.1.1\n") == []


# ── plan_dns_changes ─────────────────────────────────────────────────────── #


def test_replace_reconciles_against_the_device():
    to_remove, to_add = plan_dns_changes(
        ["10.0.0.1", "10.0.0.2"], ["10.0.0.1", "8.8.8.8"], "replace")
    # 10.0.0.1 is already right, so it is left alone.
    assert to_remove == ["8.8.8.8"]
    assert to_add == ["10.0.0.2"]


def test_replace_is_idempotent():
    assert plan_dns_changes(["10.0.0.1"], ["10.0.0.1"], "replace") == ([], [])


def test_append_never_removes():
    to_remove, to_add = plan_dns_changes(["10.0.0.1"], ["8.8.8.8"], "append")
    assert to_remove == []
    assert to_add == ["10.0.0.1"]


def test_append_skips_servers_already_present():
    assert plan_dns_changes(["8.8.8.8"], ["8.8.8.8"], "append") == ([], [])


def test_duplicate_input_is_collapsed():
    assert plan_dns_changes(["1.1.1.1", "1.1.1.1"], [], "replace") == ([], ["1.1.1.1"])


# ── build_common_setting_commands ────────────────────────────────────────── #


def test_empty_bundle_produces_no_commands():
    settings = CommonSettings()
    assert settings.is_empty
    assert build_common_setting_commands(settings, []) == []


def test_only_selected_settings_are_sent():
    """The whole point: push DNS without touching anything else."""
    cmds = [c for c, _ in build_common_setting_commands(
        CommonSettings(dns_servers=["10.0.0.1"]), [])]
    assert cmds == ["ADDDNS 10.0.0.1"]


@pytest.mark.parametrize("settings", [
    CommonSettings(dns_servers=["10.0.0.1"]),
    CommonSettings(timezone="33"),
    CommonSettings(ntp_server="pool.ntp.org", sync_time=True),
    CommonSettings(timezone="33", ntp_server="a.b", dns_servers=["1.1.1.1"],
                   web_port=8080, secure_web_port=8443, fips_mode="OFF",
                   user_login_attempts=5, user_lockout_time="1m",
                   login_attempts=20, lockout_time="5m"),
])
def test_never_emits_per_device_network_commands(settings):
    """No bundle may ever produce an IP/mask/gateway/hostname/DHCP change."""
    cmds = [c for c, _ in build_common_setting_commands(settings, ["8.8.8.8"])]
    for cmd in cmds:
        assert not any(cmd.startswith(bad) for bad in PER_DEVICE_COMMANDS), cmd


def test_command_order_and_content():
    settings = CommonSettings(
        timezone="33", ntp_server="pool.ntp.org", sync_time=True,
        dns_servers=["10.0.0.1"], web_port=8080, fips_mode="ON",
    )
    cmds = [c for c, _ in build_common_setting_commands(
        settings, ["8.8.8.8"], now=datetime(2026, 8, 21, 14, 30, 5))]
    assert cmds == [
        "TIMEZONE 33",
        "TIMEDATE 14:30:05 08-21-2026",
        "SNTP SERVER:pool.ntp.org",
        "SNTP SYNC",
        "REMDNS 8.8.8.8",
        "ADDDNS 10.0.0.1",
        "WEBPORT 8080",
        "FIPSMODE ON",
    ]


def test_sync_time_alone_still_syncs():
    cmds = [c for c, _ in build_common_setting_commands(
        CommonSettings(sync_time=True), [], now=datetime(2026, 1, 2, 3, 4, 5))]
    assert cmds == ["TIMEDATE 03:04:05 01-02-2026", "SNTP SYNC"]


def test_ntp_change_syncs_once_not_twice():
    cmds = [c for c, _ in build_common_setting_commands(
        CommonSettings(ntp_server="a.b", sync_time=True), [])]
    assert cmds.count("SNTP SYNC") == 1


def test_zero_is_not_treated_as_unset():
    """0 is a real value for these fields and must still be sent."""
    cmds = [c for c, _ in build_common_setting_commands(
        CommonSettings(user_login_attempts=0, web_port=0), [])]
    assert "SETUSERLOGINATTEMPTS 0" in cmds
    assert "WEBPORT 0" in cmds


def test_needs_reboot_only_for_fips():
    assert CommonSettings(fips_mode="ON").needs_reboot
    assert not CommonSettings(timezone="33").needs_reboot


# ── apply_common_settings ────────────────────────────────────────────────── #


class FakeSSH:
    """Records commands instead of talking to a device."""

    def __init__(self, ipconfig: str = CRESTRON_STYLE, model: str = "CP4"):
        self.ipconfig = ipconfig
        self.model = model
        self.sent: list[str] = []

    def __call__(self, *args, **kwargs):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def send_command(self, cmd, timeout=None, label=""):
        self.sent.append(cmd)
        return self.ipconfig if cmd.startswith("IPCONFIG") else ""


@pytest.fixture
def fake_ssh(monkeypatch):
    def _install(ipconfig=CRESTRON_STYLE):
        ssh = FakeSSH(ipconfig)
        monkeypatch.setattr("crestron_setup.provisioning.CrestronSSH", ssh)
        return ssh
    return _install


def test_apply_reads_current_dns_then_reconciles(fake_ssh):
    ssh = fake_ssh()
    result = apply_common_settings(
        Device(ip="10.0.0.5"), "admin", "pw",
        CommonSettings(dns_servers=["10.0.0.1"]), Config(),
    )
    assert result.success
    assert ssh.sent == ["IPCONFIG /ALL", "REMDNS 8.8.8.8", "ADDDNS 10.0.0.1"]
    assert result.current_dns == ["8.8.8.8"]


def test_apply_skips_ipconfig_in_append_mode(fake_ssh):
    """Append needs no knowledge of the current list, so save the round trip."""
    ssh = fake_ssh()
    apply_common_settings(
        Device(ip="10.0.0.5"), "admin", "pw",
        CommonSettings(dns_servers=["10.0.0.1"], dns_mode="append"), Config(),
    )
    assert ssh.sent == ["ADDDNS 10.0.0.1"]


def test_apply_skips_ipconfig_when_dns_untouched(fake_ssh):
    ssh = fake_ssh()
    apply_common_settings(Device(ip="10.0.0.5"), "admin", "pw",
                          CommonSettings(timezone="33"), Config())
    assert ssh.sent == ["TIMEZONE 33"]


def test_dry_run_sends_nothing_but_reports_commands(fake_ssh):
    ssh = fake_ssh()
    result = apply_common_settings(
        Device(ip="10.0.0.5"), "admin", "pw",
        CommonSettings(dns_servers=["10.0.0.1"], timezone="33"), Config(),
        dry_run=True,
    )
    assert result.success
    # Only the read-only IPCONFIG probe was issued.
    assert ssh.sent == ["IPCONFIG /ALL"]
    assert result.commands == ["TIMEZONE 33", "REMDNS 8.8.8.8", "ADDDNS 10.0.0.1"]


def test_dry_run_surfaces_the_detected_dns_for_verification(fake_ssh):
    """The operator needs to see what the parser read off a real device."""
    fake_ssh(WINDOWS_STYLE)
    result = apply_common_settings(
        Device(ip="10.0.0.5"), "admin", "pw",
        CommonSettings(dns_servers=["10.0.0.1"]), Config(), dry_run=True,
    )
    assert result.current_dns == ["10.0.0.1", "10.0.0.2"]


def test_apply_is_a_noop_when_already_correct(fake_ssh):
    ssh = fake_ssh()
    result = apply_common_settings(
        Device(ip="10.0.0.5"), "admin", "pw",
        CommonSettings(dns_servers=["8.8.8.8"]), Config(),
    )
    assert result.success
    assert result.detail == "Already up to date"
    assert ssh.sent == ["IPCONFIG /ALL"]


def test_empty_bundle_never_connects(monkeypatch):
    def explode(*args, **kwargs):
        raise AssertionError("should not connect for an empty bundle")
    monkeypatch.setattr("crestron_setup.provisioning.CrestronSSH", explode)
    result = apply_common_settings(Device(ip="10.0.0.5"), "admin", "pw",
                                   CommonSettings(), Config())
    assert result.success
    assert result.detail == "Nothing to apply"


def test_apply_reports_failure_without_raising(monkeypatch):
    def explode(*args, **kwargs):
        raise OSError("connection refused")
    monkeypatch.setattr("crestron_setup.provisioning.CrestronSSH", explode)
    result = apply_common_settings(Device(ip="10.0.0.5"), "admin", "pw",
                                   CommonSettings(timezone="33"), Config())
    assert not result.success
    assert "connection refused" in result.detail


def test_apply_records_model_from_the_session(fake_ssh):
    fake_ssh()
    device = Device(ip="10.0.0.5")
    apply_common_settings(device, "admin", "pw",
                          CommonSettings(timezone="33"), Config())
    assert device.model == "CP4"


def test_fips_result_mentions_the_reboot(fake_ssh):
    fake_ssh()
    result = apply_common_settings(Device(ip="10.0.0.5"), "admin", "pw",
                                   CommonSettings(fips_mode="ON"), Config())
    assert "reboot" in result.detail.lower()


# ── _is_ipv4 ─────────────────────────────────────────────────────────────── #


@pytest.mark.parametrize("value", ["10.0.0.1", "8.8.8.8", "255.255.255.255", "0.0.0.0"])
def test_is_ipv4_accepts_valid(value):
    assert cli._is_ipv4(value)


@pytest.mark.parametrize("value", [
    "10.0.0", "10.0.0.1.1", "256.1.1.1", "10.0.0.-1", "ten.0.0.1",
    "", "10.0.0.01", "10.0.0.1 ", "dns.example.com",
])
def test_is_ipv4_rejects_invalid(value):
    assert not cli._is_ipv4(value)


# ── The interactive flow ─────────────────────────────────────────────────── #
#
# These drive _flow_bulk_apply_settings with scripted prompt answers. Prompt
# order is: which-settings checkbox -> timezone -> ntp -> dns -> dns mode ->
# ports/lockout -> fips -> run mode. A blank DNS answer skips the dns-mode
# prompt.


class _Answer:
    def __init__(self, value):
        self.value = value

    def ask(self):
        return self.value


@pytest.fixture
def flow(monkeypatch):
    """Run the bulk-settings flow with scripted answers; return the sessions."""
    sessions: list[FakeSSH] = []

    class Recording(FakeSSH):
        def __init__(self, *args, **kwargs):
            super().__init__(CRESTRON_STYLE)
            sessions.append(self)

        def __call__(self, *args, **kwargs):  # not used as a factory here
            return self

    monkeypatch.setattr("crestron_setup.provisioning.CrestronSSH", Recording)
    # Never touch the user's real config file from a test.
    monkeypatch.setattr(cli, "save_config", lambda cfg: None)

    def _run(answers, devices=None, config=None):
        queue = list(answers)

        def take(*args, **kwargs):
            assert queue, f"flow asked for more input than scripted: {args[:1]}"
            return _Answer(queue.pop(0))

        for name in ("select", "checkbox", "text", "confirm", "password", "path"):
            monkeypatch.setattr(cli.questionary, name, take)

        devs = devices if devices is not None else [
            Device(ip="10.0.0.5"), Device(ip="10.0.0.6")]
        cli._flow_bulk_apply_settings(devs, "admin", "pw", config or Config())
        assert not queue, f"scripted answers left unused: {queue}"
        return sessions

    return _run


def test_flow_pushes_dns_ntp_and_timezone_to_every_device(flow):
    sessions = flow([
        ["dns_servers", "ntp_server", "timezone"],
        "033", "pool.ntp.org", "10.0.0.1, 10.0.0.2", "replace", "apply",
    ])
    assert len(sessions) == 2
    for s in sessions:
        assert s.sent == [
            "IPCONFIG /ALL", "TIMEZONE 033",
            "SNTP SERVER:pool.ntp.org", "SNTP SYNC",
            "REMDNS 8.8.8.8", "ADDDNS 10.0.0.1", "ADDDNS 10.0.0.2",
        ]


def test_flow_never_sends_per_device_network_commands(flow):
    sessions = flow([
        ["dns_servers", "ntp_server", "timezone"],
        "033", "pool.ntp.org", "10.0.0.1", "replace", "apply",
    ])
    assert sessions
    for s in sessions:
        for cmd in s.sent:
            assert not any(cmd.startswith(bad) for bad in PER_DEVICE_COMMANDS), cmd


def test_flow_dry_run_only_reads(flow):
    sessions = flow([["dns_servers"], "10.0.0.1", "replace", "dry_run"])
    assert len(sessions) == 2
    for s in sessions:
        assert s.sent == ["IPCONFIG /ALL"]


def test_flow_blank_dns_does_not_wipe_dns(flow):
    """Leaving DNS blank must not be read as 'remove every DNS server'."""
    sessions = flow([["dns_servers", "timezone"], "033", "", "apply"])
    assert sessions, "the run should still reach the devices"
    for s in sessions:
        assert not any("DNS" in cmd for cmd in s.sent), s.sent
        assert "TIMEZONE 033" in s.sent


def test_flow_rejects_invalid_dns_before_connecting(flow):
    assert flow([["dns_servers"], "10.0.0.999"]) == []


def test_flow_with_nothing_selected_is_a_noop(flow):
    assert flow([[]]) == []


def test_flow_cancel_applies_nothing(flow):
    assert flow([["timezone"], "033", "cancel"]) == []


def test_flow_remembers_dns_servers_in_config(flow):
    config = Config()
    flow([["dns_servers"], "10.0.0.1, 10.0.0.2", "replace", "apply"],
         config=config)
    assert config.dns_servers == ["10.0.0.1", "10.0.0.2"]
