<#
.SYNOPSIS
    Crestron Processor Setup Script (PowerShell)
    Automates: account creation, time/NTP config, web ports, FIPS mode,
               public key auth, firmware upload via SSH/SFTP.

.DESCRIPTION
    Runs five sequential phases against a target Crestron processor:
      1. Account Creation   - SSH as 'crestron' (first-boot) or fall back to existing credentials
      2. Public Key Upload  - SFTP .pub key to /user/ on the processor
      3. Configuration      - Timezone, NTP, web ports, lockout, FIPS, VER -V
      4. Firmware Upload     - Compare PUF versions; upload .puf only if newer
      5. Reboot             - Send REBOOT, poll until back online

    Requires the Posh-SSH module: Install-Module -Name Posh-SSH -Scope CurrentUser

.PARAMETER Host
    The hostname or IP address of the Crestron processor.

.EXAMPLE
    .\setup_processor.ps1 -Host mc4
    .\setup_processor.ps1 192.168.1.100
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0, HelpMessage = "Hostname or IP of the Crestron processor")]
    [string]$HostName
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# =============================================================================
# Configuration constants
# =============================================================================
$FirmwareDir = Join-Path $env:USERPROFILE "Sync\Crestron Firmware"
$PubKeyFile  = Join-Path $env:USERPROFILE ".ssh\id_rsa.pub"
$Timezone    = "33"           # 33 = GMT Standard Time (use TIMEZONE LIST on processor)
$NtpServer   = "pool.ntp.org"
$WebPort     = "8080"
$SecureWebPort = "8443"

# =============================================================================
# Helper functions
# =============================================================================

function Write-Status {
    <#
    .SYNOPSIS
        Write a status message with a coloured prefix tag.
    #>
    param(
        [ValidateSet("OK", "INFO", "WARN", "SKIP", "FAIL")]
        [string]$Tag,
        [string]$Message
    )
    $color = switch ($Tag) {
        "OK"   { "Green"   }
        "INFO" { "Cyan"    }
        "WARN" { "Yellow"  }
        "SKIP" { "Yellow"  }
        "FAIL" { "Red"     }
    }
    Write-Host "[$Tag] " -ForegroundColor $color -NoNewline
    Write-Host $Message
}

function Write-Phase {
    <#
    .SYNOPSIS
        Print a phase header.
    #>
    param([string]$Title)
    Write-Host ""
    Write-Host "==== $Title ====" -ForegroundColor White
}

function Write-Step {
    <#
    .SYNOPSIS
        Print a configuration step header.
    #>
    param([string]$Title)
    Write-Host "--- $Title ---" -ForegroundColor DarkGray
}

function Compare-Version {
    <#
    .SYNOPSIS
        Compare two dot-separated version strings (e.g. 2.8006.00284.01).
    .OUTPUTS
        0 if equal, 1 if Version1 > Version2, 2 if Version1 < Version2.
    #>
    param(
        [string]$Version1,
        [string]$Version2
    )
    if ($Version1 -eq $Version2) { return 0 }

    $parts1 = $Version1.Split('.')
    $parts2 = $Version2.Split('.')
    $max = [Math]::Max($parts1.Count, $parts2.Count)

    for ($i = 0; $i -lt $max; $i++) {
        $p1 = if ($i -lt $parts1.Count) { [int]$parts1[$i] } else { 0 }
        $p2 = if ($i -lt $parts2.Count) { [int]$parts2[$i] } else { 0 }
        if ($p1 -gt $p2) { return 1 }
        if ($p1 -lt $p2) { return 2 }
    }
    return 0
}

function Send-SSHCommand {
    <#
    .SYNOPSIS
        Send a command to a Crestron SSH shell stream and read the response.
    #>
    param(
        [object]$Stream,
        [string]$Command,
        [int]$PauseMs = 1500
    )
    $Stream.WriteLine($Command)
    Start-Sleep -Milliseconds $PauseMs
    return $Stream.Read()
}

function Wait-ForPrompt {
    <#
    .SYNOPSIS
        Read from a shell stream until a '>' prompt appears or timeout is reached.
    #>
    param(
        [object]$Stream,
        [int]$TimeoutSeconds = 30
    )
    $accumulated = ""
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 500
        $data = $Stream.Read()
        if ($data) {
            $accumulated += $data
            if ($accumulated -match ">") {
                return $accumulated
            }
        }
    }
    return $accumulated
}

# =============================================================================
# Validate dependencies
# =============================================================================
if (-not (Get-Module -ListAvailable -Name Posh-SSH)) {
    Write-Host "ERROR: Posh-SSH module is not installed." -ForegroundColor Red
    Write-Host "Install it with: Install-Module -Name Posh-SSH -Scope CurrentUser" -ForegroundColor Yellow
    exit 1
}

Import-Module Posh-SSH -ErrorAction Stop

# Check for public key file
$SkipPubKey = $false
if (-not (Test-Path $PubKeyFile)) {
    Write-Status -Tag "WARN" -Message "Public key file not found: $PubKeyFile"
    Write-Host "       Skipping public key upload and registration."
    $SkipPubKey = $true
    $PubKeyBasename = ""
} else {
    $PubKeyBasename = Split-Path $PubKeyFile -Leaf
}

# =============================================================================
# Prompt for new admin credentials
# =============================================================================
$NewUser = Read-Host "New admin username"
if ([string]::IsNullOrWhiteSpace($NewUser)) {
    Write-Host "ERROR: Username cannot be empty." -ForegroundColor Red
    exit 1
}

while ($true) {
    $NewPassSecure = Read-Host "New admin password" -AsSecureString
    $NewPassConfirm = Read-Host "Confirm password" -AsSecureString

    # Convert to plain text for comparison
    $bstr1 = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($NewPassSecure)
    $pass1 = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr1)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr1)

    $bstr2 = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($NewPassConfirm)
    $pass2 = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr2)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr2)

    if ($pass1 -eq $pass2) {
        break
    }
    Write-Host "Passwords do not match. Try again."
}

if ([string]::IsNullOrWhiteSpace($pass1)) {
    Write-Host "ERROR: Password cannot be empty." -ForegroundColor Red
    exit 1
}

# Build credential objects
# Note: ConvertTo-SecureString -AsPlainText is required here because we need to
# reconstruct the SecureString after the comparison loop and create the first-boot
# credential with an empty password. These are interactive, user-supplied values.
$NewPassSecure = ConvertTo-SecureString $pass1 -AsPlainText -Force
$NewCredential = New-Object System.Management.Automation.PSCredential($NewUser, $NewPassSecure)

$CrestronPassSecure = New-Object System.Security.SecureString  # empty password for first-boot
$CrestronCredential = New-Object System.Management.Automation.PSCredential("crestron", $CrestronPassSecure)

# =============================================================================
# Phase 1: Initial Account Creation (with fallback)
# =============================================================================
Write-Phase "Phase 1: Account Creation"

$AccountCreated = $false

Write-Host "Attempting first-boot login as 'crestron' with empty password..."

try {
    $session = New-SSHSession -ComputerName $HostName -Credential $CrestronCredential `
        -AcceptKey -ConnectionTimeout 10 -ErrorAction Stop

    $stream = New-SSHShellStream -SessionId $session.SessionId

    # Wait for the first-boot "Username:" prompt
    $output = Wait-ForPrompt -Stream $stream -TimeoutSeconds 15

    if ($output -match "Username:") {
        # First-boot mode — provide new credentials
        $stream.WriteLine($NewUser)
        Start-Sleep -Seconds 2
        $output = $stream.Read()

        if ($output -match "Password:") {
            $stream.WriteLine($pass1)
            Start-Sleep -Seconds 2
            $output = $stream.Read()

            if ($output -match "Verify password:") {
                $stream.WriteLine($pass1)
                Start-Sleep -Seconds 2
                $output = $stream.Read()

                if ($output -match "successfully created") {
                    Write-Host ""
                    Write-Status -Tag "OK" -Message "Admin account '$NewUser' created successfully."
                    $AccountCreated = $true
                }
            }
        }
    }

    # Clean up the first-boot session
    Remove-SSHSession -SessionId $session.SessionId -ErrorAction SilentlyContinue | Out-Null

} catch {
    Write-Host ""
    Write-Status -Tag "INFO" -Message "First-boot login failed: $($_.Exception.Message)"
}

if (-not $AccountCreated) {
    Write-Status -Tag "INFO" -Message "Trying existing account '$NewUser'..."

    try {
        $session = New-SSHSession -ComputerName $HostName -Credential $NewCredential `
            -AcceptKey -ConnectionTimeout 10 -ErrorAction Stop

        $stream = New-SSHShellStream -SessionId $session.SessionId
        $output = Wait-ForPrompt -Stream $stream -TimeoutSeconds 15

        if ($output -match ">") {
            Write-Host ""
            Write-Status -Tag "OK" -Message "Account '$NewUser' already exists. Continuing with setup..."
            $AccountCreated = $true
            Send-SSHCommand -Stream $stream -Command "BYE" | Out-Null
        }

        Remove-SSHSession -SessionId $session.SessionId -ErrorAction SilentlyContinue | Out-Null

    } catch {
        Write-Status -Tag "FAIL" -Message "Cannot log in with default credentials or '$NewUser'. Aborting."
        Write-Host "       Error: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

if (-not $AccountCreated) {
    Write-Status -Tag "FAIL" -Message "Cannot log in with default credentials or '$NewUser'. Aborting."
    exit 1
}

# Small delay to let the processor settle
Start-Sleep -Seconds 2

# =============================================================================
# Phase 2: Upload Public Key via SFTP
# =============================================================================
Write-Phase "Phase 2: Upload Public Key"

if ($SkipPubKey) {
    Write-Status -Tag "SKIP" -Message "No public key file - skipping upload."
} else {
    Write-Host "Uploading '$PubKeyBasename' to /user/ on $HostName..."

    try {
        $sftpSession = New-SFTPSession -ComputerName $HostName -Credential $NewCredential `
            -AcceptKey -ConnectionTimeout 10 -ErrorAction Stop

        Set-SFTPItem -SessionId $sftpSession.SessionId -Path $PubKeyFile `
            -Destination "/user/" -Force -ErrorAction Stop

        Remove-SFTPSession -SessionId $sftpSession.SessionId -ErrorAction SilentlyContinue | Out-Null

        Write-Host ""
        Write-Status -Tag "OK" -Message "Public key uploaded."

    } catch {
        Write-Status -Tag "FAIL" -Message "Failed to upload public key via SFTP."
        Write-Host "       Error: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# =============================================================================
# Phase 3: Configuration
# =============================================================================
Write-Phase "Phase 3: Configure Processor"

$CurrentTime = Get-Date -Format "HH:mm:ss"
$CurrentDate = Get-Date -Format "MM-dd-yyyy"

$ModelName = $null
$CurrentPufVersion = $null

try {
    $session = New-SSHSession -ComputerName $HostName -Credential $NewCredential `
        -AcceptKey -ConnectionTimeout 10 -ErrorAction Stop

    $stream = New-SSHShellStream -SessionId $session.SessionId

    # Wait for initial prompt to capture model name
    $initialOutput = Wait-ForPrompt -Stream $stream -TimeoutSeconds 15
    Write-Host $initialOutput

    if ($initialOutput -match "([A-Za-z0-9-]+)>") {
        $ModelName = $Matches[1]
        Write-Step "Connected to $ModelName"
    }

    # Register the public key only if we have one
    if (-not $SkipPubKey) {
        Write-Step "Register Public Key"
        $response = Send-SSHCommand -Stream $stream -Command "ADDPUBKEYTOUSER -N:$NewUser -K:$PubKeyBasename"
        Write-Host $response
    } else {
        Write-Step "Register Public Key"
        Write-Status -Tag "SKIP" -Message "No public key file - skipping registration."
    }

    # Send configuration commands
    $commands = @(
        @{ Cmd = "TIMEZONE $Timezone";                                Label = "Set Timezone" }
        @{ Cmd = "TIMEDATE $CurrentTime $CurrentDate";               Label = "Set Date/Time" }
        @{ Cmd = "SNTP SERVER:$NtpServer";                           Label = "Configure NTP Server" }
        @{ Cmd = "SNTP SYNC";                                        Label = "Force NTP Sync" }
        @{ Cmd = "WEBPORT $WebPort";                                  Label = "Set Web Port" }
        @{ Cmd = "SECUREWEBPORT $SecureWebPort";                     Label = "Set Secure Web Port" }
        @{ Cmd = "SETUSERLOGINATTEMPTS 5";                           Label = "Set User Login Attempts" }
        @{ Cmd = "SETUSERLOCKOUTTIME 1m";                            Label = "Set User Lockout Time" }
        @{ Cmd = "SETLOGINATTEMPTS 20";                              Label = "Set Login Attempts" }
        @{ Cmd = "SETLOCKOUTTIME 5m";                                Label = "Set Lockout Time" }
        @{ Cmd = "FIPSMODE OFF";                                     Label = "Disable FIPS Mode" }
    )

    foreach ($entry in $commands) {
        Write-Step $entry.Label
        $response = Send-SSHCommand -Stream $stream -Command $entry.Cmd
        Write-Host $response
    }

    # Get version info
    Write-Step "Version Info"
    $verOutput = Send-SSHCommand -Stream $stream -Command "VER -V" -PauseMs 3000
    Write-Host $verOutput

    # Extract PUF version from output (line like "PUF: 2.8006.00284.01")
    if ($verOutput -match "PUF:\s+([\d.]+)") {
        $CurrentPufVersion = $Matches[1].Trim()
        Write-Status -Tag "INFO" -Message "Current firmware (PUF) version: $CurrentPufVersion"
    } else {
        Write-Status -Tag "WARN" -Message "Could not extract PUF version from VER -V output."
    }

    # Disconnect
    Write-Step "Disconnecting"
    Send-SSHCommand -Stream $stream -Command "BYE" | Out-Null
    Remove-SSHSession -SessionId $session.SessionId -ErrorAction SilentlyContinue | Out-Null

} catch {
    Write-Status -Tag "FAIL" -Message "Configuration phase failed."
    Write-Host "       Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

if ([string]::IsNullOrWhiteSpace($ModelName)) {
    Write-Status -Tag "FAIL" -Message "Could not detect processor model name from prompt."
    exit 1
}

Write-Host ""
Write-Status -Tag "OK" -Message "Processor model: $ModelName"
Write-Status -Tag "OK" -Message "Configuration complete."

# =============================================================================
# Phase 4: Firmware Upload
# =============================================================================
Write-Phase "Phase 4: Firmware Upload"

$ModelLower = $ModelName.ToLower()
Write-Host "Looking for firmware matching '${ModelLower}_*.puf' in $FirmwareDir..."

$SkipFirmware = $false

if (-not (Test-Path $FirmwareDir)) {
    Write-Status -Tag "FAIL" -Message "Firmware directory not found: $FirmwareDir"
    exit 1
}

$FirmwareFiles = Get-ChildItem -Path $FirmwareDir -Filter "${ModelLower}_*.puf" -File
if ($FirmwareFiles.Count -eq 0) {
    Write-Host "WARNING: No firmware file found matching '${ModelLower}_*.puf' in $FirmwareDir" -ForegroundColor Yellow
    Write-Host "Available .puf files:"
    $allPuf = Get-ChildItem -Path $FirmwareDir -Filter "*.puf" -File -ErrorAction SilentlyContinue
    if ($allPuf) {
        $allPuf | ForEach-Object { Write-Host "  $($_.Name)" }
    } else {
        Write-Host "  (none)"
    }
    exit 1
}

if ($FirmwareFiles.Count -gt 1) {
    Write-Host "Multiple firmware files found - using the most recently modified:"
    $FirmwareFile = $FirmwareFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1
} else {
    $FirmwareFile = $FirmwareFiles[0]
}

$FirmwareBasename = $FirmwareFile.Name

# Extract version from firmware filename (e.g., mc4_2.8006.00284.01.puf -> 2.8006.00284.01)
$FilePufVersion = $FirmwareBasename -replace "^${ModelLower}_", "" -replace "\.puf$", ""

Write-Host "Found firmware: $FirmwareBasename"
Write-Host "  File version:      $FilePufVersion"
Write-Host "  Processor version: $(if ($CurrentPufVersion) { $CurrentPufVersion } else { 'unknown' })"

# Compare versions - only upload if file is newer
if ($CurrentPufVersion -and $FilePufVersion) {
    $cmpResult = Compare-Version -Version1 $FilePufVersion -Version2 $CurrentPufVersion

    if ($cmpResult -eq 0) {
        Write-Host ""
        Write-Status -Tag "SKIP" -Message "Firmware versions are identical ($FilePufVersion). No upload needed."
        $SkipFirmware = $true
    } elseif ($cmpResult -eq 2) {
        Write-Host ""
        Write-Status -Tag "SKIP" -Message "Firmware in folder ($FilePufVersion) is OLDER than processor ($CurrentPufVersion). No upload needed."
        $SkipFirmware = $true
    } else {
        Write-Status -Tag "INFO" -Message "Newer firmware available: $FilePufVersion > $CurrentPufVersion"
    }
} else {
    Write-Status -Tag "WARN" -Message "Could not compare versions - uploading firmware anyway."
}

if (-not $SkipFirmware) {
    Write-Host ""
    Write-Host "Uploading firmware: $FirmwareBasename"
    Write-Host "Source: $($FirmwareFile.FullName)"
    Write-Host "Destination: /firmware/$FirmwareBasename on $HostName"
    Write-Host ""

    try {
        $sftpSession = New-SFTPSession -ComputerName $HostName -Credential $NewCredential `
            -AcceptKey -ConnectionTimeout 10 -OperationTimeout 600 -ErrorAction Stop

        Set-SFTPItem -SessionId $sftpSession.SessionId -Path $FirmwareFile.FullName `
            -Destination "/firmware/" -Force -ErrorAction Stop

        Remove-SFTPSession -SessionId $sftpSession.SessionId -ErrorAction SilentlyContinue | Out-Null

        Write-Host ""
        Write-Status -Tag "OK" -Message "Firmware uploaded successfully."

    } catch {
        Write-Host ""
        Write-Status -Tag "FAIL" -Message "Firmware upload failed."
        Write-Host "       Error: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "       Try running the firmware upload manually:" -ForegroundColor Yellow
        Write-Host "       sftp ${NewUser}@${HostName}:/firmware/ <<< 'put $($FirmwareFile.FullName)'" -ForegroundColor Yellow
        exit 1
    }
}

# =============================================================================
# Phase 5: Reboot
# =============================================================================
Write-Phase "Phase 5: Reboot"
Write-Host "Sending reboot command..."

try {
    $session = New-SSHSession -ComputerName $HostName -Credential $NewCredential `
        -AcceptKey -ConnectionTimeout 10 -ErrorAction Stop

    $stream = New-SSHShellStream -SessionId $session.SessionId
    Wait-ForPrompt -Stream $stream -TimeoutSeconds 15 | Out-Null

    Send-SSHCommand -Stream $stream -Command "REBOOT" | Out-Null

    Remove-SSHSession -SessionId $session.SessionId -ErrorAction SilentlyContinue | Out-Null

} catch {
    Write-Status -Tag "WARN" -Message "Reboot command may not have been acknowledged: $($_.Exception.Message)"
}

Write-Status -Tag "OK" -Message "Reboot command sent."

# Wait for the processor to come back up
$RebootTimeout = 300  # 5 minutes
$PollInterval  = 5

Write-Host "Waiting for processor to go offline..."
Start-Sleep -Seconds 10

Write-Host "Polling $HostName until it responds (timeout: ${RebootTimeout}s)..."

$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

while ($stopwatch.Elapsed.TotalSeconds -lt $RebootTimeout) {
    $Elapsed = [int]$stopwatch.Elapsed.TotalSeconds
    $pingOk = Test-Connection -ComputerName $HostName -Count 1 -Quiet -TimeoutSeconds 2 -ErrorAction SilentlyContinue

    if ($pingOk) {
        Write-Host "  Ping OK - checking SSH availability..."
        Start-Sleep -Seconds 5

        try {
            $checkSession = New-SSHSession -ComputerName $HostName -Credential $NewCredential `
                -AcceptKey -ConnectionTimeout 10 -ErrorAction Stop

            $checkStream = New-SSHShellStream -SessionId $checkSession.SessionId
            $checkOutput = Wait-ForPrompt -Stream $checkStream -TimeoutSeconds 10

            if ($checkOutput -match ">") {
                Send-SSHCommand -Stream $checkStream -Command "BYE" | Out-Null
                Remove-SSHSession -SessionId $checkSession.SessionId -ErrorAction SilentlyContinue | Out-Null
                Write-Status -Tag "OK" -Message "Processor is back online."
                $stopwatch.Stop()
                break
            }

            Remove-SSHSession -SessionId $checkSession.SessionId -ErrorAction SilentlyContinue | Out-Null
            Write-Host "  Ping OK but SSH not ready yet, retrying..."

        } catch {
            Write-Host "  Ping OK but SSH not ready yet, retrying..."
        }
    } else {
        $padding = " " * 20
        Write-Host "`r  Waiting... ${Elapsed}s elapsed${padding}" -NoNewline
    }

    Start-Sleep -Seconds $PollInterval
}

$Elapsed = [int]$stopwatch.Elapsed.TotalSeconds

Write-Host ""

if ($Elapsed -ge $RebootTimeout) {
    Write-Status -Tag "FAIL" -Message "Processor did not come back online within ${RebootTimeout}s."
    exit 1
}

# =============================================================================
# Summary
# =============================================================================
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  Setup complete for $ModelName @ $HostName" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  Account:      $NewUser"
if ($SkipPubKey) {
    Write-Host "  Public Key:   Skipped (not found)"
} else {
    Write-Host "  Public Key:   $PubKeyBasename"
}
Write-Host "  Timezone:     $Timezone"
Write-Host "  NTP Server:   $NtpServer"
Write-Host "  Web Port:     $WebPort"
Write-Host "  Secure Port:  $SecureWebPort"
Write-Host "  FIPS Mode:    OFF"
if ($SkipFirmware) {
    Write-Host "  Firmware:     Already up to date ($(if ($CurrentPufVersion) { $CurrentPufVersion } else { 'unknown' }))"
} else {
    Write-Host "  Firmware:     Uploaded $FirmwareBasename"
}
Write-Host "==========================================" -ForegroundColor Green
