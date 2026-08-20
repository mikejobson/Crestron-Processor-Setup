# Agent Instructions

## Project Overview

Cross-platform Python CLI application for automated Crestron processor provisioning. Discovers devices via CIP protocol, manages accounts, configures settings, and handles firmware — all through an interactive terminal console. The legacy bash script (`setup_processor.sh`) is kept for reference.

The Crestron CLI is **not** a standard shell — it uses a custom `MODEL>` prompt (e.g., `CP4>`, `MC4>`). SSH automation uses paramiko's `invoke_shell()` with channel read/write, NOT `exec_command()`.

## Key Files

- `crestron_setup/` — Python package (the main application)
  - `cli.py` — Interactive menu loop (main entry point)
  - `discovery.py` — CIP device discovery (UDP broadcast on port 41794)
  - `ssh.py` — SSH/SFTP via paramiko (`invoke_shell()` + prompt detection)
  - `provisioning.py` — 5-phase setup logic (port of `setup_processor.sh`)
  - `firmware.py` — Firmware download, version comparison, local file discovery
  - `config.py` — YAML config loading/saving with platform-aware paths
  - `models.py` — Data classes (`Device`, `Config`, `FirmwareSource`)
  - `__main__.py` — Entry point for `python -m crestron_setup`
- `config.example.yaml` — Template configuration file
- `setup_processor.sh` — Legacy bash/expect script (macOS only)
- `crestron_command_reference.md` — 414-command CLI reference from a live CP4
- `example commands.txt` — Reference log of a manual setup session

## Architecture

### Python Application (`crestron_setup/`)

**Discovery**: `discovery.py` broadcasts a 266-byte CIP packet on UDP 41794, parses `0x15` responses to extract hostname, model, firmware version, and MAC address. Requires root/admin privileges.

**SSH**: `ssh.py` uses paramiko `invoke_shell()` with prompt detection via regex `[A-Za-z0-9-]+>`. The `CrestronSSH` class wraps connect/send_command/disconnect. `CrestronFirstBoot` handles the first-boot account creation flow (crestron/empty password → Username:/Password:/Verify prompts).

**Provisioning**: `provisioning.py` runs 5 sequential phases (same as the legacy bash script):

1. **Account Creation** — Detect first-boot, create admin account or verify existing
2. **Public Key Upload** — SFTP `.pub` to `/user/`
3. **Configuration** — 12 CLI commands (ADDPUBKEYTOUSER, TIMEZONE, TIMEDATE, SNTP, ports, lockout, FIPS, VER -V)
4. **Reboot** — Send REBOOT, poll ping + SSH (300s timeout)
5. **Firmware Upload** — Version comparison + SFTP `.puf` to `/firmware/`

**Firmware**: `firmware.py` downloads from per-model URLs configured in YAML, caches in `~/.cache/crestron-setup/firmware/`, falls back to a local firmware directory.

**Config**: `config.py` loads from `~/.config/crestron-setup/config.yaml` (macOS/Linux) or `%APPDATA%\crestron-setup\config.yaml` (Windows). A local `config.yaml` takes priority.

**CLI**: `cli.py` uses `rich` (tables, progress bars) and `questionary` (arrow-key menus, checkboxes, password prompts) for the interactive console.

## Conventions

- Status output uses rich markup: `[green][OK][/green]`, `[red][FAIL][/red]`, `[cyan][INFO][/cyan]`, `[yellow][WARN][/yellow]`
- Firmware filenames follow `{model_lower}_{version}.puf` (e.g., `mc4_2.8006.00284.01.puf`)
- PUF version from `VER -V` is used for firmware version comparison
- SSH connections use `look_for_keys=False, allow_agent=False` to force password auth

## Common Pitfalls

- Crestron SSH is NOT a standard shell — `exec_command()` will not work. Must use `invoke_shell()` with channel read/write and prompt regex matching.
- `VER -V` output has **leading whitespace** — don't anchor with `^` when parsing.
- The processor needs time after reboot before SFTP is ready (SSH may respond first). Firmware uploads happen **before** the reboot phase.
- Discovery requires root/admin for UDP broadcast on port 41794.
- First-boot detection is staged and bounded (see `CrestronFirstBoot.check_first_boot`): TCP probe :443 → HTTPS check for `/createUser.html` redirect → TCP probe :22 → SSH as `crestron` with empty password. `_check_first_boot_https` is **tri-state**: True = first boot, False = definitively provisioned (skip SSH), None = inconclusive (try SSH). If the `Username:` prompt appears over SSH, it's first boot; if a `MODEL>` prompt appears, it's already configured.
- Never check first-boot state in a serial loop over discovered devices — use `CrestronFirstBoot.check_first_boot_batch` (or `cli._check_first_boot_states`), which fans out across a thread pool with a per-device time budget.

## Testing

CI (`.github/workflows/ci.yml`) runs on every pull request and on pushes to
`main`: ruff, pytest across Python 3.10–3.13, and a packaging build. It never
publishes — releasing is `release.yml`, triggered only by a `v*` tag. Run the
same checks locally before pushing:

```bash
# Create venv and install with test dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# The two gates CI enforces
pytest
ruff check .

# Run the console
python -m crestron_setup

# Discovery requires sudo
sudo .venv/bin/python -m crestron_setup

# Legacy bash script (macOS only)
bash -n setup_processor.sh
./setup_processor.sh <hostname-or-ip>
```

Tests must stay hardware-free — no real device is reachable in CI. Network
boundaries are stubbed: `httpx.get` for the web check, `_port_open` for TCP
probes, `CrestronFirstBoot.check_first_boot` for batch-level tests. Timing
assertions use generous headroom so slow runners do not flake.
