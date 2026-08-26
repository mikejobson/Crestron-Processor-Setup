"""Data models for DM-NVX device management."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class NvxDeviceInfo:
    """Basic information about a DM-NVX device retrieved via REST API."""

    ip: str
    hostname: str = ""
    model: str = ""
    serial_number: str = ""
    firmware_version: str = ""
    mac_address: str = ""
    device_mode: str = ""  # "Transmitter" or "Receiver"
    device_ready: bool = False


@dataclass
class NvxStreamInfo:
    """Multicast stream information for a DM-NVX device."""

    multicast_address: str = ""
    status: str = ""
    bitrate: int = 0
    session_initiation: str = ""  # "Auto" or "Manual"
    stream_location: str = ""


@dataclass
class NvxUsbPort:
    """USB port information for a DM-NVX device."""

    index: int = 0
    uuid: str = ""
    name: str = ""
    mode: str = ""  # "Local" or "Remote"
    paired: bool = False
    is_active: bool = False
    host_enumerated: bool = False
    transport_mode: str = ""  # "Layer2" or "Layer3"


@dataclass
class NvxDeviceStatus:
    """Aggregated status of a DM-NVX device."""

    info: NvxDeviceInfo = field(default_factory=NvxDeviceInfo)
    streams: list[NvxStreamInfo] = field(default_factory=list)
    usb_ports: list[NvxUsbPort] = field(default_factory=list)
    audio_mode: str = ""
    audio_source: str = ""
    video_source: str = ""
    leds_enabled: bool = True
    raw_device: dict = field(default_factory=dict)
