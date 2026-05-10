"""Update checking and self-update for the Crestron setup console."""

from __future__ import annotations

import os
import platform
import shutil
import stat
import sys
import tempfile
from enum import Enum, auto
from pathlib import Path

import httpx

from . import __version__

GITHUB_REPO = "mikejobson/Crestron-Processor-Setup"
RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


class InstallMethod(Enum):
    PYINSTALLER = auto()  # Standalone binary from GitHub release
    HOMEBREW = auto()
    SCOOP = auto()
    PIP = auto()  # pip / pipx / venv
    DEV = auto()  # editable install or running from source


def detect_install_method() -> InstallMethod:
    """Detect how the application was installed."""
    # PyInstaller sets sys._MEIPASS
    if getattr(sys, "_MEIPASS", None):
        # Check if it's managed by Homebrew or Scoop
        exe = Path(sys.executable).resolve()
        exe_str = str(exe)
        if "/Cellar/" in exe_str or "/homebrew/" in exe_str.lower():
            return InstallMethod.HOMEBREW
        if "\\scoop\\" in exe_str.lower():
            return InstallMethod.SCOOP
        return InstallMethod.PYINSTALLER

    # Check for Homebrew-managed Python package
    try:
        site = Path(__import__("crestron_setup").__file__).resolve()
        site_str = str(site)
        if "/Cellar/" in site_str or "/homebrew/" in site_str.lower():
            return InstallMethod.HOMEBREW
        if "\\scoop\\" in site_str.lower():
            return InstallMethod.SCOOP
    except Exception:
        pass

    # Dev install check
    if __version__ == "0.0.0-dev":
        return InstallMethod.DEV

    return InstallMethod.PIP


def check_for_update() -> tuple[str, str] | None:
    """Check GitHub for a newer release.

    Returns (latest_version, release_url) if an update is available,
    or None if already up-to-date or check fails.
    """
    try:
        resp = httpx.get(
            RELEASES_API,
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=5,
            follow_redirects=True,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    tag = data.get("tag_name", "")
    latest = tag.lstrip("v")
    current = __version__.split("+")[0]  # strip local part if any

    if not latest or not current:
        return None

    if _version_newer(latest, current):
        html_url = data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases")
        return latest, html_url

    return None


def _version_newer(latest: str, current: str) -> bool:
    """Return True if latest is strictly newer than current."""
    try:
        lat = [int(x) for x in latest.split(".")]
        cur = [int(x) for x in current.split(".")]
        return lat > cur
    except ValueError:
        return False


def update_instructions(method: InstallMethod) -> str:
    """Return user-friendly update instructions for the install method."""
    if method == InstallMethod.HOMEBREW:
        return "brew upgrade crestron-setup"
    if method == InstallMethod.SCOOP:
        return "scoop update crestron-setup"
    if method == InstallMethod.PIP:
        return "pip install --upgrade crestron-setup"
    if method == InstallMethod.PYINSTALLER:
        return "Select 'Update Now' from the menu to download the latest version."
    return "Pull the latest changes and reinstall."


def _get_asset_name() -> str:
    """Return the expected release asset name for this platform."""
    if platform.system() == "Windows":
        return "crestron-setup-windows.exe"
    return "crestron-setup-macos"


def can_self_update(method: InstallMethod) -> bool:
    """Return True if we can perform an in-place binary update."""
    if method != InstallMethod.PYINSTALLER:
        return False
    exe = Path(sys.executable)
    # Check we can write to the executable's directory
    return os.access(exe.parent, os.W_OK)


def self_update(console) -> bool:
    """Download the latest release binary and replace the current executable.

    Returns True on success, False on failure.
    """
    try:
        resp = httpx.get(
            RELEASES_API,
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=5,
            follow_redirects=True,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        console.print(f"[red][FAIL][/red] Could not fetch release info: {exc}")
        return False

    asset_name = _get_asset_name()
    download_url = None
    for asset in data.get("assets", []):
        if asset["name"] == asset_name:
            download_url = asset["browser_download_url"]
            break

    if not download_url:
        console.print(f"[red][FAIL][/red] No asset '{asset_name}' in latest release.")
        return False

    exe = Path(sys.executable).resolve()
    tag = data.get("tag_name", "unknown")

    console.print(f"[cyan][INFO][/cyan] Downloading {tag} ({asset_name})...")

    # Download to a temp file in the same directory (for atomic rename)
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=exe.parent, prefix=".crestron-setup-update-"
    )
    try:
        with httpx.stream(
            "GET", download_url, follow_redirects=True, timeout=60
        ) as stream:
            stream.raise_for_status()
            total = int(stream.headers.get("content-length", 0))
            from rich.progress import (
                BarColumn,
                DownloadColumn,
                Progress,
                TransferSpeedColumn,
            )

            with Progress(
                "[progress.description]{task.description}",
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Downloading", total=total or None)
                with os.fdopen(tmp_fd, "wb") as f:
                    for chunk in stream.iter_bytes(8192):
                        f.write(chunk)
                        progress.advance(task, len(chunk))

        # Make executable
        tmp = Path(tmp_path)
        tmp.chmod(tmp.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

        # Replace current binary
        backup = exe.with_suffix(".bak")
        shutil.move(str(exe), str(backup))
        try:
            shutil.move(str(tmp), str(exe))
        except Exception:
            # Restore backup if move fails
            shutil.move(str(backup), str(exe))
            raise
        backup.unlink(missing_ok=True)

        console.print(f"[green][OK][/green] Updated to {tag}.")
        console.print("[cyan][INFO][/cyan] Restart the application to use the new version.")
        return True
    except Exception as exc:
        console.print(f"[red][FAIL][/red] Update failed: {exc}")
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        return False
