# Crestron Processor Setup

Cross-platform interactive console for Crestron processor provisioning. Discovers devices on the LAN, creates accounts, configures settings, and manages firmware — all from a terminal menu.

## Features

- **Device Discovery** — CIP protocol broadcast (UDP 41794) finds Crestron processors on the local network, with first-boot detection
- **Interactive Console** — Arrow-key menus, checkbox device selection, animated progress tracking
- **Cross-Platform** — Python + paramiko (works on macOS, Linux, and Windows — no `expect` dependency)
- **Firmware Management** — Download firmware from configurable URLs and upload to processors
- **Firmware Audit** — Scan discovered devices, compare firmware versions, report which need updates (read-only)
- **Batch Provisioning** — Import device lists from CSV or YAML files for bulk provisioning with per-device credentials and profiles
- **Certificate Management** — Generate CSRs, install CA-signed certs, configure TLS settings, and bulk-deploy wildcard certs
- **IP Table Management** — View, add, remove, and clear master/peer CIP entries on a device with an interactive submenu
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

| Setting            | Default                  | Description                                                              |
| ------------------ | ------------------------ | ------------------------------------------------------------------------ |
| `timezone`         | `33` (GMT Standard Time) | Crestron timezone ID                                                     |
| `ntp_server`       | `pool.ntp.org`           | NTP server address                                                       |
| `pubkey_file`      | `~/.ssh/id_rsa.pub`      | SSH public key — local path or URL (e.g. `https://github.com/user.keys`) |
| `firmware_dir`     | `~/Downloads`            | Local firmware directory (fallback)                                      |
| `web_port`         | `8080`                   | Web server port                                                          |
| `secure_web_port`  | `8443`                   | Secure web server port                                                   |
| `firmware_urls`    | _(empty)_                | Per-model firmware download URLs                                         |
| `firmware_server`  | _(empty)_                | Firmware server API base URL (see below)                                 |
| `default_username` | _(empty)_                | Pre-filled username for SSH connection prompts                           |
| `ssh_key_auth`     | `true`                   | Try SSH key auth (agent + key files) before prompting for password       |

Discovery behaviour is tuned under the `discovery` key:

| Setting          | Default | Description                                                        |
| ---------------- | ------- | ------------------------------------------------------------------ |
| `timeout`        | `5`     | Seconds to listen for CIP responses                                |
| `broadcast_count`| `3`     | Number of broadcast packets to send                                |
| `probe_timeout`  | `10`    | Per-device budget (seconds) for the first-boot check               |
| `probe_workers`  | `16`    | Devices probed in parallel during the first-boot check             |

### First-Boot Detection

After discovery, every device is checked for first-boot state. The checks run in
parallel (`probe_workers`) and each device is bounded by `probe_timeout`, so an
unresponsive device no longer holds up the rest of the estate. Each device is
probed cheapest-first:

1. TCP probe of `:443` — the web check is skipped if the port is closed.
2. HTTPS `GET /` — a redirect to `/createUser.html` means first boot. A page
   that loads *without* that redirect is a definitive "already provisioned", so
   no SSH attempt is made.
3. TCP probe of `:22`, then SSH as `crestron` with an empty password looking for
   the `Username:` prompt — only when the HTTPS check was inconclusive
   (unreachable, timed out, or an error response).

On a large estate of already-provisioned devices this normally settles in step 2.
Raise `probe_workers` for bigger estates, or `probe_timeout` on slow links where
devices are being misreported as already provisioned.

### SSH Key Authentication

When `ssh_key_auth` is enabled (default), the tool tries key-based authentication before asking for a password. This works with:

- **SSH agent** — macOS Keychain, ssh-agent, 1Password, etc.
- **Key files** — `~/.ssh/id_rsa`, `~/.ssh/id_ed25519`, etc.

Since provisioning already uploads public keys to devices via `ADDPUBKEYTOUSER`, subsequent connections can authenticate automatically — no password needed.

Set `default_username` in your config to skip the username prompt too:

```yaml
default_username: "mike"
ssh_key_auth: true
```

When connecting, you'll be asked whether to enter a password or use key auth only. If key auth fails, the tool falls back to password authentication.

### Firmware Server API

If you have a firmware server that exposes a JSON metadata API, set `firmware_server` to the base URL. The app queries `{firmware_server}/{MODEL}/latest.json` and expects:

```json
{
  "version": "2.8006.00284.01",
  "originalFileName": "mc4_2.8006.00284.01.puf",
  "fileHash": "8377fadbb1318853...",
  "fileSizeBytes": 318169239,
  "compatibleModels": ["MC4"],
  "downloadUrl": "https://storage.googleapis.com/...signed-url..."
}
```

This enables version comparison without downloading the full firmware file, and verifies the SHA256 hash after download. The server is checked before falling back to per-model `firmware_urls`.

### Batch Provisioning

Import a list of devices from a CSV or YAML file for bulk provisioning. Supports per-device credentials and profile assignments.

**CSV format** (`examples/batch.csv`):

```csv
hostname,username,password,profile
192.168.1.10,admin,admin,default
192.168.1.20,,,touch-panel
192.168.1.30,,,
```

**YAML format** (`examples/batch.yaml`):

```yaml
devices:
  - hostname: 192.168.1.10
    username: admin
    password: admin
    profile: default
  - hostname: 192.168.1.20
    profile: touch-panel
  - hostname: 192.168.1.30
```

- `hostname` (or `ip` / `host`) is required
- `username`, `password`, `profile` are optional — devices without them use shared credentials/profile prompted at runtime
- Supports both provision and dry-run modes
- Runs all devices in parallel with live progress display

### Certificate Management

Manage SSL/TLS certificates on Crestron devices from the main menu:

- **View Status** — Shows current SSL mode (SELF/CA), installed webserver, intermediate, and root certificates
- **Generate CSR** — Creates a Certificate Signing Request on the device with SANs, downloads the `.csr` file via SFTP
- **Install Certificate** — Uploads `.pem`/`.cer`/`.pfx` files, installs into the correct stores (WEBSERVER, INTERMEDIATE, ROOT), activates CA-signed SSL
- **Deploy Certificate** — Available from the Discover flow to deploy the same cert (e.g. wildcard) to multiple devices in parallel
- **SSL/TLS Settings** — Configure minimum TLS version, SSL verification, and self-signed cert auto-reboot

Save CSR defaults in your config to avoid re-entering them for every device:

```yaml
csr_defaults:
  country: "GB"
  state: "England"
  locality: "London"
  organization: "Acme Corp"
  organizational_unit: "AV"
  email: "av@acme.com"

certificates:
  cert_file: "/path/to/wildcard.pfx"
  intermediate_file: "/path/to/intermediate.pem"
  root_ca_file: "/path/to/root-ca.pem"
```

### IP Table Management

View and manage CIP IP table entries on a device. Available from the main menu ("IP Table Management") or the Discover flow ("IP Table" action on a single device).

- **View IP Table** — Shows all entries in a formatted table with coloured online/offline status
- **Add Master Entry** — Add a master (gateway) entry with CIP ID and hostname or IP
- **Remove Master Entry** — Select entries to remove from a checkbox list
- **Add Peer Entry** — Add a peer entry with CIP ID, hostname/IP, and program number
- **Remove Peer Entry** — Select peer entries to remove
- **Clear IP Table** — Clear all entries for a program (with confirmation)
- **Save to Flash** — Persist changes so they survive reboots

### Configuration Profiles

Profiles let you customise provisioning for different device types. The top-level settings act as the default; named profiles override specific fields.

```yaml
profiles:
  touch-panels:
    models: ["TSW-*", "TS-*"] # Glob patterns for auto-matching
    web_port: false # false = skip this command
    secure_web_port: false
    fips_mode: false
    extra_commands: # Custom commands after standard config
      - command: "VKENABLE OFF"
        label: "Disable virtual key bar"

  locked-down:
    models: ["CP4*", "MC4*"]
    fips_mode: "ON" # Override a value
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
| `tests/`                        | Pytest suite (hardware-free — network boundaries are stubbed)|
| `config.example.yaml`           | Template configuration file                                  |
| `setup_processor.sh`            | Legacy bash script (macOS only, requires `expect`)           |
| `crestron_command_reference.md` | CLI command reference (414 commands) from a live CP4         |
| `example commands.txt`          | Reference log of a manual setup session                      |

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

pytest          # test suite
ruff check .    # lint
```

Every pull request runs lint, the test suite on Python 3.10–3.13, and a
packaging build (`.github/workflows/ci.yml`). Nothing is published from a PR —
releases are cut by pushing a `v*` tag, which triggers `release.yml`.

`release.yml` can also be re-run manually from the Actions tab
(**Run workflow**), passing the tag to release. The version is derived from the
tag by setuptools-scm, so the tag must already exist — a manual run re-drives
the pipeline for an existing tag (after a transient failure or an expired tap
token), it does not create a new version. The run fails up front if the tag is
missing or does not start with `v`.

## Legacy Bash Script

The original `setup_processor.sh` is still included for reference. It requires macOS with `expect` and takes a single hostname argument:

```bash
./setup_processor.sh <hostname-or-ip>
```
