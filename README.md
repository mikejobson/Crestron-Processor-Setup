# Crestron Processor Setup

Bash script that automates end-to-end Crestron processor provisioning via `expect`-driven SSH/SFTP sessions.

## What It Does

Runs five sequential phases against a target processor:

1. **Account Creation** — SSH as `crestron` (first-boot default) or fall back to existing credentials; creates a new admin user
2. **Public Key Upload** — SFTP your `.pub` key to `/user/` on the processor
3. **Configuration** — Sets timezone, NTP, web ports (8080/8443), login lockout policy, FIPS mode, and captures `VER -V` output
4. **Firmware Upload** — Compares local PUF version against the processor; uploads to `/firmware/` only if newer
5. **Reboot** — Sends `REBOOT` and polls until the processor is back online

## Requirements

- macOS (uses built-in `expect`)
- `ssh`, `sftp`, `ping`
- A `.pub` key file and firmware `.puf` files on disk

## Configuration

Edit the constants at the top of `setup_processor.sh`:

| Variable       | Default                        | Description                                |
| -------------- | ------------------------------ | ------------------------------------------ |
| `FIRMWARE_DIR` | `$HOME/Sync/Crestron Firmware` | Directory containing `.puf` firmware files |
| `PUBKEY_FILE`  | `$HOME/.ssh/id_rsa.pub`        | SSH public key to upload                   |
| `TIMEZONE`     | `33` (GMT Standard Time)       | Crestron timezone ID                       |
| `NTP_SERVER`   | `pool.ntp.org`                 | NTP server address                         |

## Usage

```bash
./setup_processor.sh <hostname-or-ip>
```

The script will prompt for the new admin username and password interactively.

## Files

| File                                     | Purpose                                                        |
| ---------------------------------------- | -------------------------------------------------------------- |
| `setup_processor.sh`                     | Main provisioning script                                       |
| `example commands.txt`                   | Reference log of a manual setup session                        |
| `crestron_command_reference.md`          | CLI command reference (414 commands) generated from a live CP4 |
| `.github/prompts/crestron-cli.prompt.md` | Copilot prompt for looking up CLI commands                     |

## Testing

```bash
# Syntax check
bash -n setup_processor.sh

# Lint
shellcheck setup_processor.sh

# Run against a processor
./setup_processor.sh 192.168.1.100
```
