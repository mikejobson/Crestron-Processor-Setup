# Crestron Processor Setup

Cross-platform interactive console for Crestron processor provisioning. Discovers devices on the LAN, creates accounts, configures settings, and manages firmware — all from a terminal menu.

## Features

- **Device Discovery** — CIP protocol broadcast (UDP 41794) finds Crestron processors on the local network, with first-boot detection
- **Interactive Console** — Arrow-key menus, checkbox device selection, progress bars
- **Cross-Platform** — Python + paramiko (works on macOS, Linux, and Windows — no `expect` dependency)
- **Firmware Management** — Download firmware from configurable URLs and upload to processors
- **5-Phase Provisioning**:
  1. **Account Creation** — Detects first-boot state; creates admin account or verifies existing credentials
  2. **Public Key Upload** — SFTP `.pub` key to `/user/`
  3. **Configuration** — Timezone, NTP, web ports, login lockout policy, FIPS mode
  4. **Firmware Upload** — Version comparison; uploads `.puf` to `/firmware/` only if newer
  5. **Reboot** — Sends `REBOOT` and polls until back online

## Requirements

- Python 3.10+
- Root/admin privileges for device discovery (UDP broadcast)

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e .
```

## Usage

```bash
# Launch the interactive console
python -m crestron_setup

# Discovery requires elevated privileges
sudo .venv/bin/python -m crestron_setup
```

The console presents a main menu with options to discover devices, set up a device by IP, download firmware, or edit settings.

## Configuration

Settings are stored in `~/.config/crestron-setup/config.yaml` (macOS/Linux) or `%APPDATA%\crestron-setup\config.yaml` (Windows). A local `config.yaml` in the working directory takes priority.

Copy `config.example.yaml` to get started. Key settings:

| Setting           | Default                    | Description                         |
| ----------------- | -------------------------- | ----------------------------------- |
| `timezone`        | `33` (GMT Standard Time)   | Crestron timezone ID                |
| `ntp_server`      | `pool.ntp.org`             | NTP server address                  |
| `pubkey_file`     | `~/.ssh/id_rsa.pub`        | SSH public key to upload            |
| `firmware_dir`    | `~/Sync/Crestron Firmware` | Local firmware directory (fallback) |
| `web_port`        | `8080`                     | Web server port                     |
| `secure_web_port` | `8443`                     | Secure web server port              |
| `firmware_urls`   | _(empty)_                  | Per-model firmware download URLs    |

## Files

| Path                            | Purpose                                                      |
| ------------------------------- | ------------------------------------------------------------ |
| `crestron_setup/`               | Python package — CLI, discovery, SSH, provisioning, firmware |
| `config.example.yaml`           | Template configuration file                                  |
| `setup_processor.sh`            | Legacy bash script (macOS only, requires `expect`)           |
| `crestron_command_reference.md` | CLI command reference (414 commands) from a live CP4         |
| `example commands.txt`          | Reference log of a manual setup session                      |

## Legacy Bash Script

The original `setup_processor.sh` is still included for reference. It requires macOS with `expect` and takes a single hostname argument:

```bash
./setup_processor.sh <hostname-or-ip>
```
