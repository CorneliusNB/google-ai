#Requires -Version 5.1
<#
.SYNOPSIS
  Single-entry Windows/MuMu setup, diagnostics, offer listing and optional guided stages.
.DESCRIPTION
  Defaults to read-only checks followed by explicit opt-in for EACH live billing stage.
  The original ultra0.py may automatically click Subscribe during a live stage.
  Always verify the account, current charge, renewal terms and subscription in Google Play.
.EXAMPLE
  .\run-all.ps1 -Serial emulator-5554 -Email your-address@gmail.com -ListOnly
.EXAMPLE
  .\run-all.ps1 -Serial emulator-5554 -Email your-address@gmail.com
.EXAMPLE
  .\run-all.ps1 -Serial emulator-5554 -SetupOnly
#>
[CmdletBinding()]
param(
    [string]$Email = "",
    [string]$Serial = "",
    [ValidateSet("auto", "choose", "thread")]
    [string]$ActivityMethod = "auto",
    [switch]$SetupOnly,
    [switch]$ListOnly,
    [switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Stage([string]$Message) {
    Write-Host ""
    Write-Host ("=== {0} ===" -f $Message) -ForegroundColor Cyan
}
function Note([string]$Message) {
    Write-Host $Message
}
function Stop-Workflow([string]$Reason) {
    throw $Reason
}
function Run-Command([string]$Program, [string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) {
        Stop-Workflow ("Command exited with code {0}: {1}" -f $LASTEXITCODE, $Program)
    }
}
function Read-PythonReport([string]$AccountKey) {
    $reportFile = Join-Path $PSScriptRoot ("ultra0-report\{0}.json" -f $AccountKey)
    if (-not (Test-Path -LiteralPath $reportFile)) {
        Stop-Workflow "No report produced at $reportFile"
    }
    return (Get-Content -LiteralPath $reportFile -Raw -Encoding UTF8 | ConvertFrom-Json)
}
function Confirm-Exact([string]$Prompt, [string]$Phrase) {
    $answer = Read-Host ("{0} (type exactly: {1}; anything else stops)" -f $Prompt, $Phrase)
    return ($answer -ceq $Phrase)
}

if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Detailed
    exit 0
}

$startedAt = Get-Date
Push-Location $PSScriptRoot
try {
    Stage "0. Tools"
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Stop-Workflow "Python not found. Install Python 3.10+ from python.org, reopen PowerShell, then retry."
    }
    $Python = (Get-Command python -ErrorAction Stop).Source
    Run-Command $Python @("--version")

    $adbCommand = Get-Command adb -ErrorAction SilentlyContinue
    $Adb = if ($adbCommand) { $adbCommand.Source } else { "" }
    if (-not $Adb) {
        Note "ADB is not on PATH. Locating an existing ADB or installing platform-tools."
        $adbQuery = 'import setup_env; print("ADB_RESOLVED=" + setup_env.find_adb())'
        $adbOutput = @(& $Python -c $adbQuery)
        if ($LASTEXITCODE -ne 0) {
            Stop-Workflow "ADB resolution failed. See README troubleshooting for manual installation."
        }
        foreach ($line in $adbOutput) {
            Write-Host $line
            if ($line.StartsWith("ADB_RESOLVED=")) {
                $Adb = $line.Substring("ADB_RESOLVED=".Length).Trim()
            }
        }
    }
    if (-not $Adb) {
        Stop-Workflow "adb.exe was not found. Install Android SDK platform-tools or configure PATH and retry."
    }
    $env:ADB_PATH = $Adb
    Run-Command $Adb @("version")

    Stage "1. Select an online Android device"
    $deviceLines = @(& $Adb devices)
    if ($LASTEXITCODE -ne 0) { Stop-Workflow "ADB device discovery failed." }
    $online = @(
        foreach ($line in $deviceLines) {
            if ($line -match '^\s*(\S+)\s+device\s*$') { $Matches[1] }
        }
    )
    if ($online.Count -eq 0) {
        Note ($deviceLines -join [Environment]::NewLine)
        Stop-Workflow "No online ADB devices. Start MuMu, enable ADB debugging and wait for status 'device'."
    }
    if ($Serial) {
        if ($online -cnotcontains $Serial) {
            Stop-Workflow ("Selected serial '{0}' not online. Online: {1}" -f $Serial, ($online -join ", "))
        }
    } elseif ($online.Count -eq 1) {
        $Serial = $online[0]
    } else {
        Note ("Multiple Android devices: {0}" -f ($online -join ", "))
        $Serial = Read-Host "Enter the exact ADB serial to use"
        if ($online -cnotcontains $Serial) {
            Stop-Workflow "Invalid serial. Nothing was executed on any device."
        }
    }
    Note "Using device: $Serial"
    $AndroidVersion = ((& $Adb -s $Serial shell getprop ro.build.version.release) | Out-String).Trim()
    $AndroidSdk = ((& $Adb -s $Serial shell getprop ro.build.version.sdk) | Out-String).Trim()
    $AndroidAbi = ((& $Adb -s $Serial shell getprop ro.product.cpu.abi) | Out-String).Trim()
    Note ("Android {0} (SDK {1}), ABI {2}, activity lookup {3}" -f $AndroidVersion, $AndroidSdk, $AndroidAbi, $ActivityMethod)

    Stage "2. Verify required apps"
    foreach ($package in @("com.android.vending", "com.google.android.apps.subscriptions.red")) {
        $apk = ((& $Adb -s $Serial shell pm path $package) | Out-String).Trim()
        if ($apk -notmatch 'package:') {
            Stop-Workflow ("Android package missing or disabled: {0}. Install/enable it in MuMu." -f $package)
        }
        Note ("Installed: {0}" -f $package)
    }

    Stage "3. Python / ROOT / Frida / Play Store check"
    Note "The original ultra0.py may repair Frida and change emulator proxy/network settings."
    Run-Command $Python @("ultra0.py", "--check", "--serial", $Serial)

    if ($SetupOnly) {
        Note "Setup complete. No offers queried; no purchase requested."
        return
    }

    Stage "4. Read current Google Play account"
    $accountCode = "import sys; import ultra0 as u; u.ADB=u.find_adb(); u.pick_device(preferred=sys.argv[1]); print('PLAY_ACCOUNT='+ (u.current_play_account() or ''))"
    $accountOutput = @(& $Python -c $accountCode $Serial)
    $playAccount = ""
    if ($LASTEXITCODE -eq 0) {
        foreach ($line in $accountOutput) {
            if ($line -match '^PLAY_ACCOUNT=(.*)$') {
                $playAccount = $Matches[1].Trim().ToLowerInvariant()
            }
        }
    }
    if ($playAccount) { Note ("Detected Play Store account: {0}" -f $playAccount) }
    else { Write-Warning "Could not read Google Play account. Open the Play Store profile menu in MuMu." }

    Stage "5. Read-only offer listing"
    # The script's --list mode only queries product details; it does not call launchBillingFlow.
    Run-Command $Python @("ultra0.py", "--account", "current@device", "--no-add",
                            "--list", "--plan", "pro12", "--serial", $Serial,
                            "--activity-method", $ActivityMethod)
    $offerReport = Read-PythonReport "current"
    if ($offerReport.status -ne "listed") {
        Stop-Workflow ("Offer query did not complete: {0}" -f $offerReport.status)
    }
    Note ""
    Note "Returned first pricing phases (NOT proof of eligibility, stacking or future charges):"
    foreach ($offer in @($offerReport.offers)) {
        Note ("  {0,-24} {1,-7} {2}" -f [string]$offer.id, [string]$offer.period, [string]$offer.micros)
    }
    Note "Offer tokens are intentionally not displayed."

    Stage "6. Optional read-only Activity diagnostic"
    $pid = ((& $Adb -s $Serial shell pidof com.google.android.apps.subscriptions.red) | Out-String).Trim()
    if ($pid -match '^\d+$') {
        & $Python "scripts/diagnose-activity.py" "--serial" $Serial
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "ActivityThread diagnostic did not pass. This does not prove the chosen lookup method is broken."
        }
    } else {
        Write-Warning "Google One is not running for the optional Activity probe. Open it in MuMu and rerun this check."
    }
    if ($ListOnly) {
        Note "Read-only run complete. No purchase requested."
        return
    }

    Stage "7. Explicitly opt in to a live billing stage"
    Note "CAUTION: ultra0.py is not a harmless preview. It can automatically press Subscribe."
    Note "An offer with micros=0 may still have later paid phases, and stacking 12+6+6 months is UNVERIFIED."
    Note "No live stage will run until you enter two explicit confirmations."

    if (-not $Email) { $Email = Read-Host "Google Play account email for LIVE operation (Enter to stop)" }
    $Email = $Email.Trim().ToLowerInvariant()
    if ($Email -notmatch '^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$') {
        Note "No valid email supplied; stopping before live billing."
        return
    }
    if (-not $playAccount -or $playAccount -cne $Email) {
        $accountMismatch = ("Play account mismatch or unverified. Detected '{0}', expected '{1}'. " +
                            "Open Google Play profile and rerun; --force is intentionally not used.")
        Stop-Workflow ($accountMismatch -f $playAccount, $Email)
    }

    $stages = @(
        [pscustomobject]@{ Number = 1; Name = "Claimed 12-month offer"; Plan = "pro12"; Stack = $false },
        [pscustomobject]@{ Number = 2; Name = "Claimed additional 6 months"; Plan = "pro6"; Stack = $true },
        [pscustomobject]@{ Number = 3; Name = "Claimed additional 6 months"; Plan = "pro6b"; Stack = $true }
    )
    $key = $Email.Split('@')[0]
    foreach ($stage in $stages) {
        Stage ("Stage {0}: {1}" -f $stage.Number, $stage.Name)
        Note "Before proceeding, check today's price, future charges, cancellation and renewal terms."
        if (-not (Confirm-Exact "Run this LIVE stage?" ("RUN {0}" -f $stage.Number))) { break }
        if (-not (Confirm-Exact "The original script MAY auto-press Subscribe and initiate charges." ("I ACCEPT {0}" -f $stage.Number))) { break }

        $args = @("ultra0.py", "--account", $Email, "--no-add", "--no-switch",
                  "--plan", $stage.Plan, "--serial", $Serial, "--activity-method", $ActivityMethod)
        if ($stage.Stack) { $args += "--stack" }
        Run-Command $Python $args

        $report = Read-PythonReport $key
        Note ("Python stage status: {0}" -f $report.status)
        if ($report.status -notin @("launched", "subscribed")) {
            Note "Billing stage did not report a completed launch. No further stage will run."
            if ($report.PSObject.Properties.Name -contains "error") { Note ([string]$report.error) }
            break
        }
        Note "Check Google Play Store > Payments & subscriptions > Subscriptions."
        Note "Verify the EXACT effective end date and upcoming charge in Google's official UI."
        Note "The script's status alone does NOT confirm the requested free period."
        if (-not (Confirm-Exact "Only if the Google Play subscription is correct, continue?" "VERIFIED")) {
            break
        }
    }

    Stage "Finished"
    Note "Review your Google Play subscription status directly; no claimed duration is guaranteed."
}
catch {
    Write-Host ""
    Write-Host ("Stopped: {0}" -f $_.Exception.Message) -ForegroundColor Red
    exit 1
}
finally {
    Pop-Location
}
