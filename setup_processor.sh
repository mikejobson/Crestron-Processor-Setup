#!/bin/bash
set -euo pipefail

# =============================================================================
# Crestron Processor Setup Script
# Automates: account creation, time/NTP config, web ports, FIPS mode,
#            public key auth, firmware upload via expect-driven SSH/SFTP.
# =============================================================================

# ---- Configuration constants ------------------------------------------------
FIRMWARE_DIR="$HOME/Sync/Crestron Firmware"
PUBKEY_FILE="$HOME/.ssh/id_rsa.pub"
TIMEZONE="33"          # 33 = GMT Standard Time (use TIMEZONE LIST on processor to see options)
NTP_SERVER="pool.ntp.org"
WEB_PORT="8080"
SECURE_WEB_PORT="8443"

# ---- SSH options used throughout --------------------------------------------
SSH_OPTS="-o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 -o PubkeyAuthentication=no"

# ---- Version comparison helper ----------------------------------------------
# Compare two dot-separated version strings (e.g., 2.8006.00284.01)
# Returns: 0 if equal, 1 if v1 > v2, 2 if v1 < v2
version_compare() {
    local v1="$1" v2="$2"
    if [[ "$v1" == "$v2" ]]; then return 0; fi
    local IFS='.'
    read -ra parts1 <<< "$v1"
    read -ra parts2 <<< "$v2"
    local max=$(( ${#parts1[@]} > ${#parts2[@]} ? ${#parts1[@]} : ${#parts2[@]} ))
    for (( i=0; i<max; i++ )); do
        local p1=${parts1[$i]:-0}
        local p2=${parts2[$i]:-0}
        # Remove leading zeros for numeric comparison
        p1=$((10#$p1))
        p2=$((10#$p2))
        if (( p1 > p2 )); then return 1; fi
        if (( p1 < p2 )); then return 2; fi
    done
    return 0
}

# ---- Validate dependencies --------------------------------------------------
for cmd in expect ssh sftp ping; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: Required command '$cmd' not found." >&2
        exit 1
    fi
done

# ---- Validate arguments -----------------------------------------------------
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <processor-hostname-or-ip>"
    exit 1
fi

HOST="$1"

# ---- Check for public key file ----------------------------------------------
SKIP_PUBKEY=false
if [[ ! -f "$PUBKEY_FILE" ]]; then
    echo "[WARN] Public key file not found: $PUBKEY_FILE"
    echo "       Skipping public key upload and registration."
    SKIP_PUBKEY=true
    PUBKEY_BASENAME=""
else
    PUBKEY_BASENAME="$(basename "$PUBKEY_FILE")"
fi

# ---- Prompt for new admin credentials ---------------------------------------
read -rp "New admin username: " NEW_USER
if [[ -z "$NEW_USER" ]]; then
    echo "ERROR: Username cannot be empty." >&2
    exit 1
fi

while true; do
    read -rsp "New admin password: " NEW_PASS
    echo
    read -rsp "Confirm password: " NEW_PASS_CONFIRM
    echo
    if [[ "$NEW_PASS" == "$NEW_PASS_CONFIRM" ]]; then
        break
    fi
    echo "Passwords do not match. Try again."
done

if [[ -z "$NEW_PASS" ]]; then
    echo "ERROR: Password cannot be empty." >&2
    exit 1
fi

# =============================================================================
# Phase 1: Initial Account Creation (with fallback)
# =============================================================================
echo ""
echo "==== Phase 1: Account Creation ===="

ACCOUNT_CREATED=false

echo "Attempting first-boot login as 'crestron' with empty password..."

PHASE1_RESULT=$(expect -c "
    log_user 1
    set timeout 30
    spawn ssh $SSH_OPTS crestron@$HOST

    expect {
        \"password:\" {
            send \"\r\"
            exp_continue
        }
        \"Permission denied*\" {
            puts \"AUTH_FAILED\"
            exit 1
        }
        \"Connection refused\" {
            puts \"CONN_REFUSED\"
            exit 1
        }
        \"Connection closed\" {
            puts \"CONN_CLOSED\"
            exit 1
        }
        \"Username:\" {
            send \"$NEW_USER\r\"
        }
        timeout {
            puts \"TIMEOUT\"
            exit 1
        }
    }

    expect {
        \"Password:\" {
            send \"$NEW_PASS\r\"
        }
        timeout {
            puts \"TIMEOUT\"
            exit 1
        }
    }

    expect {
        \"Verify password:\" {
            send \"$NEW_PASS\r\"
        }
        timeout {
            puts \"TIMEOUT\"
            exit 1
        }
    }

    expect {
        \"successfully created\" {
            puts \"ACCOUNT_CREATED\"
        }
        timeout {
            puts \"TIMEOUT\"
            exit 1
        }
    }

    # Wait for connection to close
    expect eof
    exit 0
" 2>&1) || true

echo "$PHASE1_RESULT" | grep -v '^spawn ' | grep -v '^$'

if echo "$PHASE1_RESULT" | grep -q "ACCOUNT_CREATED"; then
    echo ""
    echo "[OK] Admin account '$NEW_USER' created successfully."
    ACCOUNT_CREATED=true
else
    echo ""
    echo "[INFO] First-boot login failed. Trying existing account '$NEW_USER'..."

    FALLBACK_RESULT=$(expect -c "
        log_user 1
        set timeout 15
        spawn ssh $SSH_OPTS $NEW_USER@$HOST

        expect {
            \"password:\" {
                send \"$NEW_PASS\r\"
            }
            timeout {
                puts \"TIMEOUT\"
                exit 1
            }
        }

        expect {
            \">\" {
                puts \"LOGIN_OK\"
                send \"BYE\r\"
            }
            \"Permission denied*\" {
                puts \"AUTH_FAILED\"
                exit 1
            }
            timeout {
                puts \"TIMEOUT\"
                exit 1
            }
        }

        expect eof
        exit 0
    " 2>&1) || true

    echo "$FALLBACK_RESULT" | grep -v '^spawn ' | grep -v '^$'

    if echo "$FALLBACK_RESULT" | grep -q "LOGIN_OK"; then
        echo ""
        echo "[OK] Account '$NEW_USER' already exists. Continuing with setup..."
        ACCOUNT_CREATED=true
    else
        echo "[FAIL] Cannot log in with default credentials or '$NEW_USER'. Aborting." >&2
        exit 1
    fi
fi

# Small delay to let the processor settle after account creation
sleep 2

# =============================================================================
# Phase 2: Upload Public Key via SFTP
# =============================================================================
echo ""
echo "==== Phase 2: Upload Public Key ===="

if [[ "$SKIP_PUBKEY" == true ]]; then
    echo "[SKIP] No public key file — skipping upload."
else
echo "Uploading '$PUBKEY_BASENAME' to /user/ on $HOST..."

SFTP_RESULT=$(expect -c "
    log_user 1
    set timeout 30
    spawn sftp $SSH_OPTS $NEW_USER@$HOST

    expect {
        \"password:\" {
            send \"$NEW_PASS\r\"
        }
        timeout {
            puts \"TIMEOUT waiting for SFTP password prompt\"
            exit 1
        }
    }

    expect {
        \"sftp>\" {
            send \"cd /user\r\"
        }
        timeout {
            puts \"TIMEOUT waiting for sftp prompt\"
            exit 1
        }
    }

    expect {
        \"sftp>\" {
            send \"put $PUBKEY_FILE\r\"
        }
        timeout {
            puts \"TIMEOUT after cd\"
            exit 1
        }
    }

    expect {
        \"sftp>\" {
            send \"bye\r\"
        }
        timeout {
            puts \"TIMEOUT after put\"
            exit 1
        }
    }

    expect eof
    exit 0
" 2>&1) || { echo "[FAIL] Failed to upload public key via SFTP." >&2; exit 1; }

echo "$SFTP_RESULT" | grep -v '^spawn ' | grep -v '^$'
echo ""
echo "[OK] Public key uploaded."
fi

# =============================================================================
# Phase 3: Configuration
# =============================================================================
echo ""
echo "==== Phase 3: Configure Processor ===="

# Build the time string from the host's clock
CURRENT_TIME=$(date +"%H:%M:%S")
CURRENT_DATE=$(date +"%m-%d-%Y")

# Helper: send a command, wait for prompt, print the response
# Uses a unique marker to delimit each command's response
CONFIG_OUTPUT=$(expect -c "
    log_user 1
    set timeout 30

    proc send_cmd {cmd label} {
        puts \"\r\n--- \$label ---\"
        send \"\$cmd\r\"
        expect \">\"
    }

    spawn ssh $SSH_OPTS $NEW_USER@$HOST

    expect {
        \"password:\" {
            send \"$NEW_PASS\r\"
        }
        timeout {
            puts \"TIMEOUT waiting for password prompt\"
            exit 1
        }
    }

    # Wait for the initial prompt — capture model name from it
    expect {
        -re \"(\[A-Za-z0-9-\]+)>\" {
            set model \$expect_out(1,string)
            puts \"\r\nMODEL_NAME=\$model\"
            puts \"--- Connected to \$model ---\"
        }
        timeout {
            puts \"TIMEOUT waiting for prompt\"
            exit 1
        }
    }

    # Register the public key only if we have one
    set skip_pubkey $SKIP_PUBKEY
    if {\$skip_pubkey ne \"true\"} {
        send_cmd \"ADDPUBKEYTOUSER -N:$NEW_USER -K:$PUBKEY_BASENAME\" \"Register Public Key\"
    } else {
        puts \"\r\n--- Register Public Key ---\"
        puts \"SKIPPED (no public key file)\"
    }

    send_cmd \"TIMEZONE $TIMEZONE\" \"Set Timezone\"
    send_cmd \"TIMEDATE $CURRENT_TIME $CURRENT_DATE\" \"Set Date/Time\"
    send_cmd \"SNTP SERVER:$NTP_SERVER\" \"Configure NTP Server\"
    send_cmd \"SNTP SYNC\" \"Force NTP Sync\"
    send_cmd \"WEBPORT $WEB_PORT\" \"Set Web Port\"
    send_cmd \"SECUREWEBPORT $SECURE_WEB_PORT\" \"Set Secure Web Port\"
    send_cmd \"SETUSERLOGINATTEMPTS 5\" \"Set User Login Attempts\"
    send_cmd \"SETUSERLOCKOUTTIME 1m\" \"Set User Lockout Time\"
    send_cmd \"SETLOGINATTEMPTS 20\" \"Set Login Attempts\"
    send_cmd \"SETLOCKOUTTIME 5m\" \"Set Lockout Time\"
    send_cmd \"FIPSMODE OFF\" \"Disable FIPS Mode\"

    # Get version info
    puts \"\r\n--- Version Info ---\"
    send \"VER -V\r\"
    expect {
        -re \"(.+)\r\n\(\[A-Za-z0-9-\]+)>\" {
            # Output captured and printed by log_user
        }
        timeout {
            puts \"TIMEOUT waiting for VER output\"
        }
    }

    # Disconnect (reboot happens later after firmware upload)
    puts \"\r\n--- Disconnecting ---\"
    send \"BYE\r\"

    expect {
        eof { }
        \"closed\" { }
        timeout { }
    }

    exit 0
" 2>&1) || true

# Print the full session output (expect's log_user already shows responses)
echo "$CONFIG_OUTPUT" | grep -v '^spawn '

# Extract model name from output
MODEL_NAME=$(echo "$CONFIG_OUTPUT" | grep -o 'MODEL_NAME=[A-Za-z0-9-]*' | head -1 | cut -d= -f2)

if [[ -z "$MODEL_NAME" ]]; then
    echo ""
    echo "[FAIL] Could not detect processor model name from prompt." >&2
    exit 1
fi

# Extract PUF version from VER -V output (line like "PUF: 2.8006.00284.01")
CURRENT_PUF_VERSION=$(echo "$CONFIG_OUTPUT" | grep -i 'PUF:' | grep -v 'PUFexec' | sed 's/^[[:space:]]*PUF:[[:space:]]*//' | tr -d '[:space:]')
if [[ -n "$CURRENT_PUF_VERSION" ]]; then
    echo "[INFO] Current firmware (PUF) version: $CURRENT_PUF_VERSION"
else
    echo "[WARN] Could not extract PUF version from VER -V output."
fi

echo ""
echo "[OK] Processor model: $MODEL_NAME"
echo "[OK] Configuration complete."

# =============================================================================
# Phase 4: Firmware Upload
# =============================================================================
echo ""
echo "==== Phase 4: Firmware Upload ===="

MODEL_LOWER=$(echo "$MODEL_NAME" | tr '[:upper:]' '[:lower:]')
echo "Looking for firmware matching '${MODEL_LOWER}_*.puf' in $FIRMWARE_DIR..."

# Find matching firmware file
FIRMWARE_FILES=()
while IFS= read -r -d '' f; do
    FIRMWARE_FILES+=("$f")
done < <(find "$FIRMWARE_DIR" -maxdepth 1 -iname "${MODEL_LOWER}_*.puf" -print0 2>/dev/null)

if [[ ${#FIRMWARE_FILES[@]} -eq 0 ]]; then
    echo "WARNING: No firmware file found matching '${MODEL_LOWER}_*.puf' in $FIRMWARE_DIR" >&2
    echo "Available .puf files:"
    ls -1 "$FIRMWARE_DIR"/*.puf 2>/dev/null || echo "  (none)"
    exit 1
fi

if [[ ${#FIRMWARE_FILES[@]} -gt 1 ]]; then
    echo "Multiple firmware files found — using the most recently modified:"
    FIRMWARE_FILE=$(ls -t "${FIRMWARE_FILES[@]}" | head -1)
else
    FIRMWARE_FILE="${FIRMWARE_FILES[0]}"
fi

FIRMWARE_BASENAME="$(basename "$FIRMWARE_FILE")"

# Extract version from firmware filename (e.g., mc4_2.8006.00284.01.puf -> 2.8006.00284.01)
FILE_PUF_VERSION=$(echo "$FIRMWARE_BASENAME" | sed "s/^${MODEL_LOWER}_//i" | sed 's/\.puf$//')

echo "Found firmware: $FIRMWARE_BASENAME"
echo "  File version:      $FILE_PUF_VERSION"
echo "  Processor version: ${CURRENT_PUF_VERSION:-unknown}"

SKIP_FIRMWARE=false

# Compare versions — only upload if the file is newer
if [[ -n "$CURRENT_PUF_VERSION" && -n "$FILE_PUF_VERSION" ]]; then
    set +e
    version_compare "$FILE_PUF_VERSION" "$CURRENT_PUF_VERSION"
    CMP_RESULT=$?
    set -e

    if [[ $CMP_RESULT -eq 0 ]]; then
        echo ""
        echo "[SKIP] Firmware versions are identical ($FILE_PUF_VERSION). No upload needed."
        SKIP_FIRMWARE=true
    elif [[ $CMP_RESULT -eq 2 ]]; then
        echo ""
        echo "[SKIP] Firmware in folder ($FILE_PUF_VERSION) is OLDER than processor ($CURRENT_PUF_VERSION). No upload needed."
        SKIP_FIRMWARE=true
    else
        echo "[INFO] Newer firmware available: $FILE_PUF_VERSION > $CURRENT_PUF_VERSION"
    fi
else
    echo "[WARN] Could not compare versions — uploading firmware anyway."
fi

if [[ "$SKIP_FIRMWARE" != true ]]; then
    echo ""
    echo "Uploading firmware: $FIRMWARE_BASENAME"
    echo "Source: $FIRMWARE_FILE"
    echo "Destination: /firmware/$FIRMWARE_BASENAME on $HOST"
    echo ""

FW_RESULT=$(expect -c "
    log_user 1
    set timeout 600
    spawn sftp $SSH_OPTS $NEW_USER@$HOST

    expect {
        \"password:\" {
            send \"$NEW_PASS\r\"
        }
        \"Connection refused\" {
            puts \"SFTP_CONNECT_FAILED\"
            exit 1
        }
        \"Connection reset\" {
            puts \"SFTP_CONNECT_FAILED\"
            exit 1
        }
        timeout {
            puts \"TIMEOUT waiting for SFTP password prompt\"
            exit 1
        }
    }

    expect {
        \"sftp>\" {
            send \"cd /firmware\r\"
        }
        \"Permission denied\" {
            puts \"SFTP_AUTH_FAILED\"
            exit 1
        }
        \"Connection closed\" {
            puts \"SFTP_CONNECT_FAILED\"
            exit 1
        }
        timeout {
            puts \"TIMEOUT waiting for sftp prompt\"
            exit 1
        }
    }

    expect {
        \"sftp>\" {
            send \"put $FIRMWARE_FILE\r\"
        }
        timeout {
            puts \"TIMEOUT after cd\"
            exit 1
        }
    }

    expect {
        \"sftp>\" {
            puts \"SFTP_UPLOAD_OK\"
            send \"bye\r\"
        }
        timeout {
            puts \"TIMEOUT after put — firmware upload may have timed out\"
            exit 1
        }
    }

    expect eof
    exit 0
" 2>&1)

echo "$FW_RESULT" | grep -v '^spawn ' | grep -v '^$'

if echo "$FW_RESULT" | grep -q "SFTP_UPLOAD_OK"; then
    echo ""
    echo "[OK] Firmware uploaded successfully."
elif echo "$FW_RESULT" | grep -q "SFTP_CONNECT_FAILED\|SFTP_AUTH_FAILED"; then
    echo ""
    echo "[FAIL] SFTP connection failed." >&2
    echo "       Try running the firmware upload manually:" >&2
    echo "       sftp $NEW_USER@$HOST:/firmware/ <<< 'put $FIRMWARE_FILE'" >&2
    exit 1
else
    echo ""
    echo "[FAIL] Firmware upload failed. Check output above for details." >&2
    exit 1
fi

fi  # end SKIP_FIRMWARE check

# =============================================================================
# Phase 5: Reboot
# =============================================================================
echo ""
echo "==== Phase 5: Reboot ===="
echo "Sending reboot command..."

expect -c "
    log_user 1
    set timeout 30
    spawn ssh $SSH_OPTS $NEW_USER@$HOST

    expect {
        \"password:\" {
            send \"$NEW_PASS\r\"
        }
        timeout {
            puts \"TIMEOUT waiting for password prompt\"
            exit 1
        }
    }

    expect {
        \">\" {
            send \"REBOOT\r\"
        }
        timeout {
            puts \"TIMEOUT waiting for prompt\"
            exit 1
        }
    }

    expect {
        eof { }
        \"closed\" { }
        timeout { }
    }

    exit 0
" 2>&1 || true

echo "[OK] Reboot command sent."

# Wait for the processor to come back up
REBOOT_TIMEOUT=300  # 5 minutes
POLL_INTERVAL=5
ELAPSED=0

echo "Waiting for processor to go offline..."
sleep 10

echo "Polling $HOST until it responds (timeout: ${REBOOT_TIMEOUT}s)..."
while [[ $ELAPSED -lt $REBOOT_TIMEOUT ]]; do
    if ping -c1 -W2 "$HOST" &>/dev/null; then
        echo "  Ping OK — checking SSH availability..."
        sleep 5
        SSH_CHECK=$(expect -c "
            log_user 0
            set timeout 10
            spawn ssh $SSH_OPTS $NEW_USER@$HOST
            expect {
                \"password:\" {
                    send \"$NEW_PASS\r\"
                }
                timeout {
                    exit 1
                }
            }
            expect {
                \">\" {
                    send \"BYE\r\"
                    puts \"SSH_READY\"
                }
                timeout {
                    exit 1
                }
            }
            expect eof
            exit 0
        " 2>&1) || true

        if echo "$SSH_CHECK" | grep -q "SSH_READY"; then
            echo "[OK] Processor is back online."
            break
        else
            echo "  Ping OK but SSH not ready yet, retrying..."
        fi
    else
        printf "  Waiting... %ds elapsed\r" "$ELAPSED"
    fi
    sleep "$POLL_INTERVAL"
    ELAPSED=$((ELAPSED + POLL_INTERVAL + 2))
done
echo ""

if [[ $ELAPSED -ge $REBOOT_TIMEOUT ]]; then
    echo "[FAIL] Processor did not come back online within ${REBOOT_TIMEOUT}s." >&2
    exit 1
fi

echo ""
echo "=========================================="
echo "  Setup complete for $MODEL_NAME @ $HOST"
echo "=========================================="
echo "  Account:      $NEW_USER"
if [[ "$SKIP_PUBKEY" == true ]]; then
    echo "  Public Key:   Skipped (not found)"
else
    echo "  Public Key:   $PUBKEY_BASENAME"
fi
echo "  Timezone:     $TIMEZONE"
echo "  NTP Server:   $NTP_SERVER"
echo "  Web Port:     $WEB_PORT"
echo "  Secure Port:  $SECURE_WEB_PORT"
echo "  FIPS Mode:    OFF"
if [[ "$SKIP_FIRMWARE" == true ]]; then
    echo "  Firmware:     Already up to date (${CURRENT_PUF_VERSION:-unknown})"
else
    echo "  Firmware:     Uploaded $FIRMWARE_BASENAME"
fi
echo "=========================================="
