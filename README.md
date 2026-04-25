# Crestron Processor Setup

Scripts that automate end-to-end Crestron processor provisioning via SSH/SFTP. Available as a **Bash** script (macOS/Linux) and a **PowerShell** script (Windows).

## What It Does

Runs five sequential phases against a target processor:

1. **Account Creation** — SSH as `crestron` (first-boot default) or fall back to existing credentials; creates a new admin user
2. **Public Key Upload** — SFTP your `.pub` key to `/user/` on the processor
3. **Configuration** — Sets timezone, NTP, web ports (8080/8443), login lockout policy, FIPS mode, and captures `VER -V` output
4. **Firmware Upload** — Compares local PUF version against the processor; uploads to `/firmware/` only if newer
5. **Reboot** — Sends `REBOOT` and polls until the processor is back online

## Requirements

### Bash (macOS/Linux)

- macOS or Linux (uses built-in `expect`)
- `ssh`, `sftp`, `ping`
- A `.pub` key file and firmware `.puf` files on disk

### PowerShell (Windows)

- PowerShell 5.1+ or PowerShell 7+
- [Posh-SSH](https://github.com/darkoperator/Posh-SSH) module — install with:
  ```powershell
  Install-Module -Name Posh-SSH -Scope CurrentUser
  ```
- A `.pub` key file and firmware `.puf` files on disk

## Configuration

Edit the constants at the top of `setup_processor.sh` (Bash) or `setup_processor.ps1` (PowerShell):

| Variable (Bash)  | Variable (PowerShell) | Default                        | Description                                |
| ----------------- | --------------------- | ------------------------------ | ------------------------------------------ |
| `FIRMWARE_DIR`    | `$FirmwareDir`        | `~/Sync/Crestron Firmware`     | Directory containing `.puf` firmware files |
| `PUBKEY_FILE`     | `$PubKeyFile`         | `~/.ssh/id_rsa.pub`           | SSH public key to upload                   |
| `TIMEZONE`        | `$Timezone`           | `33` (GMT Standard Time)       | Crestron timezone ID                       |
| `NTP_SERVER`      | `$NtpServer`          | `pool.ntp.org`                 | NTP server address                         |

## Usage

### Bash

```bash
./setup_processor.sh <hostname-or-ip>
```

### PowerShell

```powershell
.\setup_processor.ps1 -HostName <hostname-or-ip>
# or positionally:
.\setup_processor.ps1 mc4
```

Both scripts will prompt for the new admin username and password interactively.

## Files

| File                                     | Purpose                                                         |
| ---------------------------------------- | --------------------------------------------------------------- |
| `setup_processor.sh`                     | Main provisioning script (Bash/macOS/Linux)                     |
| `setup_processor.ps1`                    | Main provisioning script (PowerShell/Windows)                   |
| `example commands.txt`                   | Reference log of a manual setup session                         |
| `crestron_command_reference.md`          | CLI command reference (414 commands) generated from a live CP4  |
| `.github/prompts/crestron-cli.prompt.md` | Copilot prompt for looking up CLI commands                      |

## Testing

### Bash

```bash
# Syntax check
bash -n setup_processor.sh

# Lint
shellcheck setup_processor.sh

# Run against a processor
./setup_processor.sh 192.168.1.100
```

### PowerShell

```powershell
# Syntax check (parses without executing)
$null = [System.Management.Automation.Language.Parser]::ParseFile(
    (Resolve-Path .\setup_processor.ps1),
    [ref]$null, [ref]$errors
)
$errors  # empty = no syntax errors

# Lint (if PSScriptAnalyzer is installed)
Invoke-ScriptAnalyzer -Path .\setup_processor.ps1

# Run against a processor
.\setup_processor.ps1 -HostName 192.168.1.100
```
