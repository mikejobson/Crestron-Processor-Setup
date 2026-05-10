# Crestron Processor Setup

Cross-platform interactive console for Crestron processor provisioning. Discovers devices on the LAN, creates accounts, configures settings, and manages firmware — all from a terminal menu.

## Features

- **Device Discovery** — CIP protocol broadcast (UDP 41794) finds Crestron processors on the local network, with first-boot detection
- **Interactive Console** — Arrow-key menus, checkbox device selection, animated progress tracking
- **Cross-Platform** — Python + paramiko (works on macOS, Linux, and Windows — no `expect` dependency)
- **Firmware Management** — Download firmware from configurable URLs and upload to processors
- **Network Configuration** — Set static IP or DHCP per device during provisioning
- **Restore & Erase** — Factory-reset devices with `initialize` + `restore` commands
- **6-Phase Provisioning**:
  1. **Account Creation** — Detects first-boot state; creates admin account or verifies existing credentials
  2. **Public Key Upload** — SFTP `.pub` key to `/user/`
  3. **Configuration** — Timezone, NTP, web ports, login lockout policy, FIPS mode
  4. **Network Configuration** — DHCP or static IP with subnet, gateway, and DNS
  5. **Reboot** — Sends `REBOOT` and polls until back online
  6. **Firmware Upload** — Version comparison; uploads `.puf` to `/firmware/` only if newer

## Installation

### Homebrew (macOS)

```bash
brew install mikejobson/tap/crestron-setup
```

### pip (all platforms)

```bash
pip install crestron-setup
```

### Standalone Binary

Download the latest binary from [GitHub Releases](https://github.com/mikejobson/Crestron-Processor-Setup/releases):

| Platform | Download                     |
| -------- | ---------------------------- |
| macOS    | `crestron-setup-macos`       |
| Windows  | `crestron-setup-windows.exe` |

```bash
# macOS — make executable and move to PATH
chmod +x crestron-setup-macos
sudo mv crestron-setup-macos /usr/local/bin/crestron-setup
```

### Scoop (Windows)

```powershell
scoop bucket add crestron https://github.com/mikejobson/scoop
scoop install crestron-setup
```

### From Source

```bash
git clone https://github.com/mikejobson/Crestron-Processor-Setup.git
cd Crestron-Processor-Setup
python3 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e .
```

## Requirements

- Python 3.10+ (pip and source installs only — standalone binaries are self-contained)
- Root/admin privileges for device discovery (UDP broadcast)

## Usage

```bash
# Launch the interactive console
crestron-setup

# Discovery requires elevated privileges
sudo crestron-setup

# If installed via pip / from source
python -m crestron_setup
sudo .venv/bin/python -m crestron_setup
```

## Configuration

Settings are stored in `~/.config/crestron-setup/config.yaml` (macOS/Linux) or `%APPDATA%\crestron-setup\config.yaml` (Windows). A local `config.yaml` in the working directory takes priority.

Copy `config.example.yaml` to get started. Key settings:

| Setting           | Default                    | Description                                                              |
| ----------------- | -------------------------- | ------------------------------------------------------------------------ |
| `timezone`        | `33` (GMT Standard Time)   | Crestron timezone ID                                                     |
| `ntp_server`      | `pool.ntp.org`             | NTP server address                                                       |
| `pubkey_file`     | `~/.ssh/id_rsa.pub`        | SSH public key — local path or URL (e.g. `https://github.com/user.keys`) |
| `firmware_dir`    | `~/Sync/Crestron Firmware` | Local firmware directory (fallback)                                      |
| `web_port`        | `8080`                     | Web server port                                                          |
| `secure_web_port` | `8443`                     | Secure web server port                                                   |
| `firmware_urls`   | _(empty)_                  | Per-model firmware download URLs                                         |

### Configuration Profiles

Profiles let you customise provisioning for different device types. The top-level settings act as the default; named profiles override specific fields.

```yaml
profiles:
  touch-panels:
    models: ["TSW-*", "TS-*"]    # Glob patterns for auto-matching
    web_port: false               # false = skip this command
    secure_web_port: false
    fips_mode: false
    extra_commands:                # Custom commands after standard config
      - command: "PROGCOMMENTS OFF"
        label: "Disable program comments"

  locked-down:
    models: ["CP4*", "MC4*"]
    fips_mode: "ON"               # Override a value
    user_login_attempts: 3
    user_lockout_time: "30m"
```

Key concepts:
- **`false`** = skip this command entirely (it won't be sent to the device)
- **Omitted** = inherit the default value
- **`models`** = glob patterns matched against `device.model` for auto-suggestion
- **`extra_commands`** = custom CLI commands run after standard phase 3 configuration

Profiles are managed interactively via **Settings → Manage Profiles**, or edited directly in `config.yaml`.

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
