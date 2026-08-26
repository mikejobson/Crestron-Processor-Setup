"""REST API client for Crestron DM-NVX AV-over-IP devices.

Reference:
  https://sdkcon78221.crestron.com/sdk/DM_NVX_REST_API/Content/Topics/API-Reference.htm

The DM-NVX REST API uses a session-cookie authentication model.
All configuration is accessed via the ``/Device`` endpoint tree
using GET (read) and POST (write) with partial JSON payloads.
"""

from __future__ import annotations

import base64
from typing import Any

import httpx

from .nvx_models import (
    NvxDeviceInfo,
    NvxDeviceStatus,
    NvxStreamInfo,
    NvxUsbPort,
)

# Endpoints under /Device
_EP_DEVICE = "/Device"
_EP_DEVICE_INFO = "/Device/DeviceInfo"
_EP_DEVICE_SPECIFIC = "/Device/DeviceSpecific"
_EP_DEVICE_OPS = "/Device/DeviceOperations"
_EP_STREAM_TX = "/Device/StreamTransmit"
_EP_STREAM_RX = "/Device/StreamReceive"
_EP_USB = "/Device/Usb"

_TIMEOUT = 15


class NvxApiError(Exception):
    """Raised when an NVX REST API call fails."""


class NvxClient:
    """Thin wrapper around the DM-NVX REST API.

    Usage::

        client = NvxClient("192.168.1.50")
        client.login("admin", "password")
        status = client.get_status()
        client.set_device_mode("Transmitter")
        client.close()
    """

    def __init__(self, host: str, *, verify_ssl: bool = False) -> None:
        self.host = host
        base = f"https://{host}"
        self._http = httpx.Client(
            base_url=base,
            verify=verify_ssl,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def login(self, username: str, password: str) -> None:
        """Authenticate and store the session cookie."""
        # The NVX API typically accepts JSON credentials at /userlogin.html
        # or /api/login.  We attempt common endpoints.
        payload = {"username": username, "password": password}

        for path in ("/userlogin.html", "/api/login"):
            try:
                resp = self._http.post(path, json=payload)
                if resp.status_code < 400:
                    return  # session cookie stored in client
            except httpx.HTTPError:
                continue

        # Fallback: HTTP basic auth for the session
        token = base64.b64encode(f"{username}:{password}".encode()).decode()
        self._http.headers["Authorization"] = f"Basic {token}"

    def close(self) -> None:
        """Close the HTTP client."""
        self._http.close()

    # ------------------------------------------------------------------
    # Raw helpers
    # ------------------------------------------------------------------

    def _get(self, path: str) -> dict[str, Any]:
        """GET a JSON endpoint, raising on errors."""
        try:
            resp = self._http.get(path)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            raise NvxApiError(
                f"GET {path} returned {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise NvxApiError(f"GET {path} failed: {exc}") from exc

    def _post(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        """POST a JSON payload, raising on errors."""
        try:
            resp = self._http.post(path, json=data)
            resp.raise_for_status()
            try:
                return resp.json()
            except ValueError:
                return {}
        except httpx.HTTPStatusError as exc:
            raise NvxApiError(
                f"POST {path} returned {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise NvxApiError(f"POST {path} failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Device info
    # ------------------------------------------------------------------

    def get_device_info(self) -> NvxDeviceInfo:
        """Retrieve basic device information."""
        data = self._get(_EP_DEVICE_INFO)
        info_raw = data.get("Device", {}).get("DeviceInfo", {})
        return NvxDeviceInfo(
            ip=self.host,
            hostname=info_raw.get("HostName", ""),
            model=info_raw.get("Model", info_raw.get("BuildModel", "")),
            serial_number=info_raw.get("SerialNumber", ""),
            firmware_version=info_raw.get("FirmwareVersion",
                                          info_raw.get("Version", "")),
            mac_address=info_raw.get("MacAddress", ""),
        )

    # ------------------------------------------------------------------
    # Device mode (Transmitter / Receiver)
    # ------------------------------------------------------------------

    def get_device_specific(self) -> dict[str, Any]:
        """Return the raw DeviceSpecific block."""
        data = self._get(_EP_DEVICE_SPECIFIC)
        return data.get("Device", {}).get("DeviceSpecific", {})

    def get_device_mode(self) -> str:
        """Return the current device mode (Transmitter / Receiver)."""
        spec = self.get_device_specific()
        return spec.get("DeviceMode", "Unknown")

    def set_device_mode(self, mode: str) -> None:
        """Set device mode to 'Transmitter' or 'Receiver'."""
        self._post(_EP_DEVICE_SPECIFIC, {
            "Device": {
                "DeviceSpecific": {
                    "DeviceMode": mode,
                }
            }
        })

    # ------------------------------------------------------------------
    # Stream / Multicast
    # ------------------------------------------------------------------

    def get_transmit_streams(self) -> list[NvxStreamInfo]:
        """Get transmit stream information."""
        data = self._get(_EP_STREAM_TX)
        raw_streams = (
            data.get("Device", {})
            .get("StreamTransmit", {})
            .get("Streams", [])
        )
        return [self._parse_stream(s) for s in raw_streams]

    def get_receive_streams(self) -> list[NvxStreamInfo]:
        """Get receive stream information."""
        data = self._get(_EP_STREAM_RX)
        raw_streams = (
            data.get("Device", {})
            .get("StreamReceive", {})
            .get("Streams", [])
        )
        return [self._parse_stream(s) for s in raw_streams]

    @staticmethod
    def _parse_stream(raw: dict[str, Any]) -> NvxStreamInfo:
        return NvxStreamInfo(
            multicast_address=raw.get("MulticastAddress", ""),
            status=raw.get("Status", ""),
            bitrate=raw.get("Bitrate", 0),
            session_initiation=raw.get("SessionInitiation", ""),
            stream_location=raw.get("StreamLocation", ""),
        )

    def set_multicast_address(
        self,
        address: str,
        *,
        stream_index: int = 0,
        direction: str = "transmit",
    ) -> None:
        """Set the multicast address on a stream.

        Args:
            address: Multicast IP address (e.g. ``239.x.x.x``).
            stream_index: Stream index (usually 0).
            direction: ``"transmit"`` or ``"receive"``.
        """
        stream_data: dict[str, Any] = {"MulticastAddress": address}

        # Build the Streams array with the correct index
        streams: list[dict[str, Any]] = []
        for i in range(stream_index + 1):
            streams.append(stream_data if i == stream_index else {})

        if direction == "transmit":
            key = "StreamTransmit"
            endpoint = _EP_STREAM_TX
        else:
            key = "StreamReceive"
            endpoint = _EP_STREAM_RX

        self._post(endpoint, {"Device": {key: {"Streams": streams}}})

    # ------------------------------------------------------------------
    # USB
    # ------------------------------------------------------------------

    def get_usb_ports(self) -> list[NvxUsbPort]:
        """Retrieve USB port information."""
        data = self._get(_EP_USB)
        raw_ports = (
            data.get("Device", {}).get("Usb", {}).get("UsbPorts", [])
        )
        ports = []
        for i, p in enumerate(raw_ports):
            ports.append(NvxUsbPort(
                index=i,
                uuid=p.get("Uuid", ""),
                name=p.get("Name", ""),
                mode=p.get("Mode", ""),
                paired=bool(p.get("Paired", False)),
                is_active=bool(p.get("IsActive", False)),
                host_enumerated=bool(p.get("HostEnumerated", False)),
                transport_mode=p.get("TransportMode",
                                     p.get("UsbPairing", {}).get(
                                         "TransportMode", "")),
            ))
        return ports

    def set_usb_mode(self, mode: str, *, port_index: int = 0) -> None:
        """Set USB mode to 'Local' or 'Remote' on a port."""
        ports: list[dict[str, Any]] = []
        for i in range(port_index + 1):
            ports.append({"Mode": mode} if i == port_index else {})

        self._post(_EP_USB, {
            "Device": {"Usb": {"UsbPorts": ports}},
        })

    def set_usb_transport(
        self, transport: str, *, port_index: int = 0,
    ) -> None:
        """Set USB transport mode ('Layer2' or 'Layer3')."""
        pairing: dict[str, Any] = {}
        if transport == "Layer2":
            pairing["Layer2"] = {}
        else:
            pairing["Layer3"] = {}

        ports: list[dict[str, Any]] = []
        for i in range(port_index + 1):
            ports.append(
                {"UsbPairing": pairing} if i == port_index else {}
            )

        self._post(_EP_USB, {
            "Device": {"Usb": {"UsbPorts": ports}},
        })

    def pair_usb(
        self, remote_device_id: str, *, port_index: int = 0,
    ) -> None:
        """Pair a USB port with a remote device UUID."""
        ports: list[dict[str, Any]] = []
        for i in range(port_index + 1):
            if i == port_index:
                ports.append({"Pair": remote_device_id})
            else:
                ports.append({})

        self._post(_EP_USB, {
            "Device": {"Usb": {"UsbPorts": ports}},
        })

    def unpair_usb(self, *, port_index: int = 0) -> None:
        """Unpair a USB port."""
        ports: list[dict[str, Any]] = []
        for i in range(port_index + 1):
            ports.append({"Unpair": True} if i == port_index else {})

        self._post(_EP_USB, {
            "Device": {"Usb": {"UsbPorts": ports}},
        })

    # ------------------------------------------------------------------
    # Device operations
    # ------------------------------------------------------------------

    def reboot(self) -> None:
        """Reboot the device."""
        self._post(_EP_DEVICE_OPS, {
            "Device": {"DeviceOperations": {"Reboot": True}},
        })

    # ------------------------------------------------------------------
    # Aggregated status
    # ------------------------------------------------------------------

    def get_status(self) -> NvxDeviceStatus:
        """Retrieve aggregated device status."""
        info = self.get_device_info()
        spec = self.get_device_specific()

        info.device_mode = spec.get("DeviceMode", "Unknown")
        info.device_ready = bool(spec.get("DeviceReady", False))

        # Fetch streams based on mode
        if info.device_mode == "Transmitter":
            streams = self.get_transmit_streams()
        elif info.device_mode == "Receiver":
            streams = self.get_receive_streams()
        else:
            # Unknown mode — try transmit first, then receive
            streams = self.get_transmit_streams()
            if not streams:
                streams = self.get_receive_streams()

        usb_ports = self.get_usb_ports()

        return NvxDeviceStatus(
            info=info,
            streams=streams,
            usb_ports=usb_ports,
            audio_mode=spec.get("AudioMode", ""),
            audio_source=spec.get("AudioSource", ""),
            video_source=spec.get("VideoSource", ""),
            leds_enabled=bool(spec.get("LedsEnabled", True)),
        )
