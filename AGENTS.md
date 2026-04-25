# Agent Instructions

## Project Overview

Bash script that automates end-to-end Crestron processor provisioning via `expect`-driven SSH/SFTP sessions. The Crestron CLI is **not** a standard shell — it uses a custom `MODEL>` prompt (e.g., `MC4>`).

## Key Files

- `setup_processor.sh` — The main (and only) script. All logic lives here.
- `example commands.txt` — Reference log of a manual setup session showing command syntax, expected prompts, and processor responses.

## Architecture

The script runs in 5 sequential phases:

1. **Account Creation** — SSH as `crestron` (first-boot) or fall back to existing credentials
2. **Public Key Upload** — SFTP `.pub` file to `/user/` on the processor
3. **Configuration** — SSH session sending CLI commands (timezone, NTP, ports, lockout, FIPS, VER -V)
4. **Firmware Upload** — Compare PUF versions; SFTP `.puf` to `/firmware/` only if newer
5. **Reboot** — SSH to send `REBOOT`, poll until back online

## Conventions

- All SSH/SFTP automation uses `expect` (macOS built-in). The Crestron CLI prompt is `MODEL>` — match on `>` for expect patterns.
- Configuration constants are at the top of the script: `FIRMWARE_DIR`, `PUBKEY_FILE`, `TIMEZONE`, `NTP_SERVER`.
- Status output uses `[OK]`, `[INFO]`, `[WARN]`, `[SKIP]`, `[FAIL]` prefixes. Each phase prints `==== Phase N: Title ====`. Config commands print `--- Step Name ---` headers.
- Firmware filenames follow the pattern `{model_lower}_{version}.puf` (e.g., `mc4_2.8006.00284.01.puf`). The PUF version from `VER -V` output is used for comparison.
- SSH options: `-o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 -o PubkeyAuthentication=no`

## Common Pitfalls

- Crestron `VER -V` output has **leading whitespace** on most lines — don't anchor grep with `^` when extracting values.
- After `expect` runs, check output for success markers (e.g., `SFTP_UPLOAD_OK`) rather than trusting exit codes — `expect` can exit 0 even when SSH/SFTP connections fail.
- The processor needs time after reboot before SFTP is ready (SSH may respond first). That's why firmware uploads happen **before** the reboot phase.

## Testing

```bash
# Syntax check
bash -n setup_processor.sh

# Lint (if installed)
shellcheck setup_processor.sh

# Run against a processor
./setup_processor.sh <hostname-or-ip>
```
