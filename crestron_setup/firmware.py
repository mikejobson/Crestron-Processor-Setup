"""Firmware discovery, download, and version comparison."""

from __future__ import annotations

import os
import platform
import re
import zipfile
from dataclasses import dataclass
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

# Firmware filename pattern: {model}_{version}.puf or .zip
FW_PATTERN = re.compile(r"^(.+?)_([\d.]+)\.puf$", re.IGNORECASE)
FW_ZIP_PATTERN = re.compile(r"^(.+?)_([\d.]+(?:_r\d+)?)\.zip$", re.IGNORECASE)


# --------------------------------------------------------------------------- #
#  Firmware server API
# --------------------------------------------------------------------------- #


@dataclass
class FirmwareServerInfo:
    """Metadata returned by the firmware server API."""

    version: str
    filename: str
    file_hash: str
    file_size: int
    download_url: str
    compatible_models: list[str]


def query_firmware_server(
    model: str, server_url: str
) -> FirmwareServerInfo | None:
    """Query the firmware server API for the latest firmware metadata.

    Fetches {server_url}/{MODEL}/latest.json and parses the response.
    Returns None if the server is not configured, unreachable, or has no
    firmware for this model.
    """
    if not server_url:
        return None

    url = f"{server_url.rstrip('/')}/{model.upper()}/latest.json"
    try:
        resp = httpx.get(url, timeout=15, follow_redirects=True)
        resp.raise_for_status()
        data = resp.json()
        return FirmwareServerInfo(
            version=data.get("version", ""),
            filename=data.get("originalFileName", ""),
            file_hash=data.get("fileHash", ""),
            file_size=int(data.get("fileSizeBytes", 0)),
            download_url=data.get("downloadUrl", ""),
            compatible_models=data.get("compatibleModels", []),
        )
    except Exception:
        return None


def download_from_server(
    info: FirmwareServerInfo,
    console: Console | None = None,
) -> Path | None:
    """Download firmware using the signed URL from the firmware server.

    Verifies the SHA256 hash after download if provided.
    When console is None, runs silently (used by download_firmware_quiet).
    Returns the local path or None on failure.
    """
    if not info.download_url:
        return None

    cache = _cache_dir()
    cache.mkdir(parents=True, exist_ok=True)

    dest_name = info.filename or f"firmware_{info.version}.puf"
    dest = cache / dest_name

    # Skip download if we already have this exact file
    if dest.exists() and info.file_hash:
        existing_hash = _sha256_file(dest)
        if existing_hash == info.file_hash:
            if console:
                console.print(
                    f"[green][OK][/green] Already cached: {dest.name} (hash verified)"
                )
            return dest

    try:
        if console:
            console.print(f"Downloading {dest_name}…")

        with httpx.stream(
            "GET", info.download_url, follow_redirects=True, timeout=300
        ) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0)) or info.file_size or None

            if console:
                with Progress(
                    TextColumn("[bold]{task.description}"),
                    BarColumn(),
                    DownloadColumn(),
                    TransferSpeedColumn(),
                    console=console,
                ) as progress:
                    task = progress.add_task(dest_name, total=total)
                    with open(dest, "wb") as f:
                        for chunk in resp.iter_bytes(chunk_size=65536):
                            f.write(chunk)
                            progress.advance(task, len(chunk))
            else:
                with open(dest, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=65536):
                        f.write(chunk)

        # Verify hash
        if info.file_hash:
            actual_hash = _sha256_file(dest)
            if actual_hash != info.file_hash:
                if console:
                    console.print(
                        f"[red][FAIL][/red] Hash mismatch — expected {info.file_hash[:16]}…, "
                        f"got {actual_hash[:16]}…"
                    )
                dest.unlink()
                return None

        if console:
            console.print(f"[green][OK][/green] Downloaded: {dest.name}")
            if info.file_hash:
                console.print(f"  [dim]SHA256 verified[/dim]")
        return dest

    except httpx.HTTPStatusError as e:
        if console:
            console.print(f"[red][FAIL][/red] HTTP {e.response.status_code}: {e}")
    except httpx.RequestError as e:
        if console:
            console.print(f"[red][FAIL][/red] Download failed: {e}")
    except Exception as e:
        if console:
            console.print(f"[red][FAIL][/red] Unexpected error: {e}")
        if dest.exists():
            dest.unlink()

    return None


def _sha256_file(path: Path) -> str:
    """Compute SHA256 hex digest of a file."""
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


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


def cache_info() -> tuple[Path, list[tuple[Path, int]]]:
    """Return the cache directory and a list of (path, size_bytes) for cached files."""
    cache = _cache_dir()
    files: list[tuple[Path, int]] = []
    if cache.exists():
        for f in sorted(cache.iterdir()):
            if f.is_file():
                files.append((f, f.stat().st_size))
    return cache, files


def clear_cache(paths: list[Path] | None = None) -> int:
    """Delete cached firmware files. If paths is None, delete all. Returns count deleted."""
    cache = _cache_dir()
    if not cache.exists():
        return 0
    count = 0
    targets = paths if paths is not None else [f for f in cache.iterdir() if f.is_file()]
    for f in targets:
        try:
            f.unlink()
            count += 1
        except OSError:
            pass
    return count


def _parse_puf_metadata(puf_path: Path) -> tuple[str, list[str]]:
    """Read firmware metadata from a PUF or ZIP firmware file.

    PUF files contain ~.package.ini with DeviceSelectionLogic lines.
    ZIP firmware files contain ~info.ini with Version= and Targets= lines.

    Returns (version, supported_models) where supported_models is a list
    of model strings.
    """
    version = ""
    models: list[str] = []

    try:
        with zipfile.ZipFile(puf_path, "r") as zf:
            names = zf.namelist()

            # Try PUF-style ~.package.ini first
            ini_names = [n for n in names if n.endswith(".package.ini")]
            if ini_names:
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
                            for token in tokens[1:]:
                                m = token.strip()
                                if m and m.upper() not in [x.upper() for x in models]:
                                    models.append(m)

                return version, models

            # Try ZIP firmware-style ~info.ini (e.g. NVX devices)
            info_names = [n for n in names if n.lower().endswith("info.ini")]
            if info_names:
                ini_text = zf.read(info_names[0]).decode("utf-8", errors="replace")

                for line in ini_text.splitlines():
                    line = line.strip()
                    if line.startswith("//"):
                        continue

                    # Version=7.4.0255.22319
                    if line.lower().startswith("version=") and not version:
                        version = line.split("=", 1)[1].strip()

                    # Targets=DM-NVX-384,DM-NVX-384C,DM-NVX-385,DM-NVX-385C
                    if line.lower().startswith("targets="):
                        targets = line.split("=", 1)[1].strip()
                        for t in targets.split(","):
                            t = t.strip()
                            if t and t.upper() not in [x.upper() for x in models]:
                                models.append(t)

                return version, models

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
            if not f.is_file() or f.suffix.lower() not in (".puf", ".zip"):
                continue

            # Try INI-based matching first (works for both PUF and ZIP firmware)
            version, supported = _parse_puf_metadata(f)
            if supported:
                if model_upper in [m.upper() for m in supported]:
                    candidates.append((f, version))
                continue

            # Fallback to filename pattern matching
            m = FW_PATTERN.match(f.name)
            if m and m.group(1).lower() == model.lower():
                candidates.append((f, m.group(2)))
                continue

            # Try ZIP firmware filename pattern
            m = FW_ZIP_PATTERN.match(f.name)
            if m and m.group(1).lower() == model.lower():
                candidates.append((f, m.group(2).split("_")[0]))

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
    """Download firmware for a model from the configured sources.

    Checks firmware server API first (if configured), then falls back to
    per-model firmware_urls.  Returns the local path or None on failure.
    """
    # Try firmware server API first
    if config.firmware_server:
        info = query_firmware_server(model, config.firmware_server)
        if info and info.download_url:
            console.print(f"[cyan][INFO][/cyan] Firmware server: {model} v{info.version}")
            result = download_from_server(info, console=console)
            if result:
                return result
            console.print("[yellow][WARN][/yellow] Server download failed, trying direct URL…")

    # Fall back to per-model direct URL
    source = config.firmware_urls.get(model.upper())
    if not source or not source.url:
        if not config.firmware_server:
            console.print(
                f"[yellow][WARN][/yellow] No download URL configured for {model}.\n"
                "  Add one to your config.yaml under firmware_urls\n"
                "  or set firmware_server for API-based downloads."
            )
        return None

    cache = _cache_dir()
    cache.mkdir(parents=True, exist_ok=True)

    # Derive initial filename from URL (may be overridden by Content-Disposition)
    url_filename = source.url.rstrip("/").split("/")[-1]
    if not url_filename.lower().endswith((".puf", ".zip")):
        url_filename = f"{model.lower()}_latest.puf"

    console.print(f"Downloading firmware for {model}...")
    console.print(f"  URL:  {source.url}")

    try:
        with httpx.stream(
            "GET", source.url, headers=source.headers, follow_redirects=True, timeout=300
        ) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))

            # Use Content-Disposition filename if available
            cd = resp.headers.get("content-disposition", "")
            real_name = ""
            if cd:
                import re as _re
                # Try filename*= (RFC 5987) first, then filename=
                m = _re.search(r"filename\*\s*=\s*(?:UTF-8''|utf-8'')(.+?)(?:;|$)", cd)
                if not m:
                    m = _re.search(r'filename\s*=\s*"?([^";]+)"?', cd)
                if m:
                    from urllib.parse import unquote
                    real_name = unquote(m.group(1)).strip()

            dest_name = real_name if real_name and real_name.lower().endswith((".puf", ".zip")) else url_filename
            dest = cache / dest_name
            console.print(f"  Dest: {dest}")

            with Progress(
                TextColumn("[bold]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(dest_name, total=total or None)
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


def download_firmware_quiet(
    model: str,
    config: Config,
) -> Path | None:
    """Download firmware for a model silently (no console output).

    Used during provisioning to auto-download when no local file exists.
    Checks firmware server API first, then falls back to per-model URLs.
    Returns the local path to the downloaded file, or None on failure.
    """
    # Try firmware server API first (silent)
    if config.firmware_server:
        info = query_firmware_server(model, config.firmware_server)
        if info and info.download_url:
            result = download_from_server(info, console=None)
            if result:
                return result

    # Fall back to per-model direct URL
    source = config.firmware_urls.get(model.upper())
    if not source or not source.url:
        return None

    cache = _cache_dir()
    cache.mkdir(parents=True, exist_ok=True)

    url_filename = source.url.rstrip("/").split("/")[-1]
    if not url_filename.lower().endswith((".puf", ".zip")):
        url_filename = f"{model.lower()}_latest.puf"

    try:
        with httpx.stream(
            "GET", source.url, headers=source.headers, follow_redirects=True, timeout=300
        ) as resp:
            resp.raise_for_status()

            # Use Content-Disposition filename if available
            cd = resp.headers.get("content-disposition", "")
            real_name = ""
            if cd:
                import re as _re
                m = _re.search(r"filename\*\s*=\s*(?:UTF-8''|utf-8'')(.+?)(?:;|$)", cd)
                if not m:
                    m = _re.search(r'filename\s*=\s*"?([^";]+)"?', cd)
                if m:
                    from urllib.parse import unquote
                    real_name = unquote(m.group(1)).strip()

            dest_name = real_name if real_name and real_name.lower().endswith((".puf", ".zip")) else url_filename
            dest = cache / dest_name

            with open(dest, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=65536):
                    f.write(chunk)

        return dest

    except Exception:
        return None
