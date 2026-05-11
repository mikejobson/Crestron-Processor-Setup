# Copilot Instructions

## Build & Run

```bash
# Install from source (editable)
python3 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e .

# Run the interactive console
python -m crestron_setup

# Discovery requires elevated privileges (UDP broadcast)
sudo .venv/bin/python -m crestron_setup

# Syntax-check the legacy bash script
bash -n setup_processor.sh
```

Versioning uses `setuptools-scm` — the version is derived from git tags automatically. No manual version bumps.

## Architecture

Cross-platform Python CLI for automated Crestron processor provisioning. The entry point is `crestron_setup/cli.py:main()`, which presents an interactive menu using `rich` and `questionary`.

### Core flow

1. **Discovery** (`discovery.py`) — Broadcasts a 266-byte CIP packet on UDP 41794, parses `0x15` responses to extract hostname, model, firmware, and MAC. Requires root/admin.
2. **SSH** (`ssh.py`) — All Crestron SSH uses paramiko `invoke_shell()` with channel read/write. The CLI prompt is `MODEL>` (e.g. `CP4>`, `MC4>`), matched by regex `[A-Za-z0-9][-A-Za-z0-9]*[A-Za-z0-9]>`.
3. **Provisioning** (`provisioning.py`) — 6-phase sequential setup: account creation → pubkey upload → configuration → network config → reboot → firmware upload.
4. **Firmware** (`firmware.py`) — Downloads from per-model URLs or a firmware server API, caches in `~/.cache/crestron-setup/firmware/`, falls back to a local directory.
5. **Config** (`config.py`) — Loads YAML from `~/.config/crestron-setup/config.yaml` (macOS/Linux) or `%APPDATA%\crestron-setup\config.yaml` (Windows). A local `config.yaml` takes priority.

### Data model

All data classes live in `models.py`: `Device`, `Config`, `Profile`, `ResolvedProfile`, `FirmwareSource`, `ExtraCommand`, `CsrDefaults`, `CertificateConfig`. Profiles use a `SKIP` sentinel (Python `object()`, YAML `false`) to indicate a setting should not be sent to the device. `resolve_profile()` merges a named profile with default config.

## Key Conventions

- **Crestron SSH is not a standard shell.** Never use `exec_command()` — it will silently fail. Always use `invoke_shell()` with channel `recv()`/`send()` and prompt regex detection.
- **Status output** uses rich markup tags: `[green][OK][/green]`, `[red][FAIL][/red]`, `[cyan][INFO][/cyan]`, `[yellow][WARN][/yellow]`.
- **Firmware filenames** follow `{model_lower}_{version}.puf` (e.g. `mc4_2.8006.00284.01.puf`).
- **`VER -V` output** has leading whitespace — never anchor version parsing with `^`.
- **SSH auth** defaults to `look_for_keys=False, allow_agent=False` to force password auth, unless `ssh_key_auth` is enabled in config.
- **First-boot detection**: HTTPS check for `/createUser.html` redirect (fast path) → SSH as `crestron` with empty password (fallback). `Username:` prompt = first boot; `MODEL>` prompt = already configured.
- **Profile override pattern**: `None` = inherit default, `SKIP` sentinel = skip command, any other value = override.
- All modules use `from __future__ import annotations` for modern type hint syntax.

## Crestron CLI Reference

`crestron_command_reference.md` contains 414 commands from a live CP4. There is also a reusable prompt at `.github/prompts/crestron-cli.prompt.md` for command lookups. Commands are case-insensitive but conventionally mixed-case (e.g. `ADDPUBKEYtouser`).

## Release Process

Releases are triggered by pushing a `v*` tag. The GitHub Actions workflow (`release.yml`) builds a wheel, publishes to PyPI via trusted publisher OIDC, builds standalone executables with PyInstaller (macOS + Windows), creates a GitHub Release, and bumps the Homebrew tap and Scoop bucket.
