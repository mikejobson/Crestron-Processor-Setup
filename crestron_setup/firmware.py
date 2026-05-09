"""Firmware discovery, download, and version comparison."""

from __future__ import annotations

import os
import platform
import re
import zipfile
from pathlib import Path

import httpx
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TransferSpeedColumn,
)

from .models import Config, FirmwareSource

# Firmware filename pattern: {model}_{version}.puf
FW_PATTERN = re.compile(r"^(.+?)_([\d.]+)\.puf$", re.IGNORECASE)


def version_compare(v1: str, v2: str) -> int:
    """Compare two dot-separated version strings.

    Returns:
        1  if v1 > v2
        0  if v1 == v2
        -1 if v1 < v2
    """
    if v1 == v2:
        return 0
    parts1 = [int(p) for p in v1.split(".")]
    parts2 = [int(p) for p in v2.split(".")]
    max_len = max(len(parts1), len(parts2))
    for i in range(max_len):
        p1 = parts1[i] if i < len(parts1) else 0
        p2 = parts2[i] if i < len(parts2) else 0
        if p1 > p2:
            return 1
        if p1 < p2:
            return -1
    return 0


def _cache_dir() -> Path:
    """Return the platform-appropriate firmware cache directory."""
    if platform.system() == "Windows":
        base = os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
        return Path(base) / "crestron-setup" / "firmware"
    return Path.home() / ".cache" / "crestron-setup" / "firmware"


def _parse_puf_metadata(puf_path: Path) -> tuple[str, list[str]]:
    """Read ~.package.ini from a PUF (ZIP) file.

    Returns (version, supported_models) where supported_models is a list
    of model strings from all DeviceSelectionLogic lines.
    """
    version = ""
    models: list[str] = []

    try:
        with zipfile.ZipFile(puf_path, "r") as zf:
            ini_names = [n for n in zf.namelist() if n.endswith(".package.ini")]
            if not ini_names:
                return version, models

            ini_text = zf.read(ini_names[0]).decode("utf-8", errors="replace")

            for line in ini_text.splitlines():
                line = line.strip()

                # Version=3.003.0015.001
                if line.lower().startswith("version=") and not version:
                    version = line.split("=", 1)[1].strip()

                # DeviceSelectionLogic=model_is_one_of,TSW-570,TS-770,...
                if "deviceselectionlogic" in line.lower() and "model_is_one_of" in line.lower():
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        tokens = parts[1].split(",")
                        # Skip the first token ("model_is_one_of")
                        for token in tokens[1:]:
                            m = token.strip()
                            if m and m.upper() not in [x.upper() for x in models]:
                                models.append(m)

    except (zipfile.BadZipFile, OSError, KeyError):
        pass

    return version, models


def find_local_firmware(
    model: str, config: Config
) -> tuple[Path | None, str]:
    """Find a firmware file for the given model in local directories.

    Searches PUF files by reading the ~.package.ini inside each ZIP to
    check if the device model is listed in DeviceSelectionLogic. Falls
    back to filename-based matching if no INI is found.

    Searches the cache directory first, then the configured firmware_dir.
    Returns (path, version) or (None, '') if not found.
    """
    model_upper = model.upper()
    candidates: list[tuple[Path, str]] = []

    search_dirs = [_cache_dir(), Path(config.firmware_dir).expanduser()]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for f in search_dir.iterdir():
            if not f.is_file() or not f.suffix.lower() == ".puf":
                continue

            # Try INI-based matching first
            version, supported = _parse_puf_metadata(f)
            if supported:
                if model_upper in [m.upper() for m in supported]:
                    candidates.append((f, version))
                continue

            # Fallback to filename pattern matching
            m = FW_PATTERN.match(f.name)
            if m and m.group(1).lower() == model.lower():
                candidates.append((f, m.group(2)))

    if not candidates:
        return None, ""

    # Return the newest version
    candidates.sort(key=lambda x: [int(p) for p in x[1].split(".") if p.isdigit()], reverse=True)
    return candidates[0]


def download_firmware(
    model: str,
    config: Config,
    console: Console,
) -> Path | None:
    """Download firmware for a model from the configured URL.

    Returns the local path to the downloaded file, or None on failure.
    """
    source = config.firmware_urls.get(model.upper())
    if not source or not source.url:
        console.print(
            f"[yellow][WARN][/yellow] No download URL configured for {model}.\n"
            "  Add one to your config.yaml under firmware_urls."
        )
        return None

    cache = _cache_dir()
    cache.mkdir(parents=True, exist_ok=True)

    # Derive filename from URL
    url_path = source.url.rstrip("/").split("/")[-1]
    if not url_path.lower().endswith(".puf"):
        url_path = f"{model.lower()}_latest.puf"
    dest = cache / url_path

    console.print(f"Downloading firmware for {model}...")
    console.print(f"  URL:  {source.url}")
    console.print(f"  Dest: {dest}")

    try:
        with httpx.stream(
            "GET", source.url, headers=source.headers, follow_redirects=True, timeout=300
        ) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))

            with Progress(
                TextColumn("[bold]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(url_path, total=total or None)
                with open(dest, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=65536):
                        f.write(chunk)
                        progress.advance(task, len(chunk))

        console.print(f"[green][OK][/green] Downloaded: {dest.name}")
        return dest

    except httpx.HTTPStatusError as e:
        console.print(f"[red][FAIL][/red] HTTP {e.response.status_code}: {e}")
    except httpx.RequestError as e:
        console.print(f"[red][FAIL][/red] Download failed: {e}")
    except Exception as e:
        console.print(f"[red][FAIL][/red] Unexpected error: {e}")
        # Clean up partial download
        if dest.exists():
            dest.unlink()

    return None
