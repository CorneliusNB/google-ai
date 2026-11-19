#Requires -Version 5.1
<#
.SYNOPSIS
  Single-entry Windows/MuMu setup, diagnostics, offer listing and optional guided stages.
.DESCRIPTION
  Defaults to original Step 1 (read-only). Original Steps 2-5 require explicit selection.
  -AllStages runs original Steps 2-5, with approval for each billable stage.
  -StartStep 3 with -AllStages skips Step 2 when a subscription is already active.
  Individual -Step 2..5 commands do not require typed confirmations.
  -AllStages retains verification prompts between potentially billable steps.
  Step 5 is the author's optional additional offer and can be skipped.
  The original ultra0.py may automatically click Subscribe during a live stage.
  Always verify the account, current charge, renewal terms and subscription in Google Play.
.EXAMPLE
  .\run-all.ps1 -Step 0               # Original environment check
.EXAMPLE
  .\run-all.ps1 -Step 1               # Original read-only offer list (default)
.EXAMPLE
  .\run-all.ps1 -Step 2 -Email account@example.com  # No typed confirmation; may purchase
.EXAMPLE
  .\run-all.ps1 -Step 5 -Email account@example.com
.EXAMPLE
  .\run-all.ps1 -AllStages                       # Original steps 2-5, with confirmation
.EXAMPLE
  .\run-all.ps1 -AllStages -Force                # Author's account-check bypass (unsafe)
.EXAMPLE
  .\run-all.ps1 -AllStages -StartStep 3         # Resume without replaying Step 2
#>
[CmdletBinding()]
param(
    [string]$Email = "",
    [string]$Serial = "",
    [ValidateRange(0,5)]
    [int]$Step = 1,
    [switch]$AllStages,
    [ValidateRange(2,5)]
    [int]$StartStep = 2,
    [switch]$Force,
    [ValidateSet("auto", "choose", "thread")]
    [string]$ActivityMethod = "auto",
    [switch]$SetupOnly,
    [switch]$ListOnly,
    [switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Show-Banner {
    Write-Host ""
    Write-Host "  +----------------------------------------------------+" -ForegroundColor DarkCyan
    Write-Host "  |  GOOGLE AI  /  MuMu Toolkit                       |" -ForegroundColor Cyan
    Write-Host "  +----------------------------------------------------+" -ForegroundColor DarkCyan
    Write-Host "  Original: @gylive   |   Maintained: @hoangsvit" -ForegroundColor DarkGray
    $mode = if ($AllStages) { "Full flow from Step $StartStep" } else { "Step $Step" }
    Write-Host ("  Mode: {0}" -f $mode) -ForegroundColor Gray
}
function Stage([string]$Message) {
    Write-Host ""
    Write-Host ("  >> {0}" -f $Message) -ForegroundColor Cyan
    Write-Host ("  {0}" -f ("-" * 56)) -ForegroundColor DarkGray
}
function Note([string]$Message) {
    Write-Host ("  {0}" -f $Message) -ForegroundColor Gray
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
function Get-RuntimeValue([string[]]$LookupArgs) {
    $output = @(& $Python "scripts/runtime-lookup.py" @LookupArgs)
    if ($LASTEXITCODE -ne 0) {
        Stop-Workflow "Runtime lookup failed. Verify the Python and ADB environment."
    }
    $resultLine = $output | Where-Object { $_ -match '^RUNTIME_RESULT:[A-Za-z0-9+/=]*$' } | Select-Object -Last 1
    if ($null -eq $resultLine) {
        Stop-Workflow "No machine-readable runtime result was returned."
    }
    $encoded = ([string]$resultLine).Substring("RUNTIME_RESULT:".Length)
    return [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($encoded))
}

function Read-PythonReport([string]$AccountKey) {
    $reportFile = Join-Path $PSScriptRoot ("ultra0-report\{0}.json" -f $AccountKey)
    if (-not (Test-Path -LiteralPath $reportFile)) {
        Stop-Workflow "No report produced at $reportFile"
    }
    return (Get-Content -LiteralPath $reportFile -Raw -Encoding UTF8 | ConvertFrom-Json)
}
function Confirm-Exact([string]$Prompt, [string]$Phrase) {
    # All approvals are numeric; 2 ends the run rather than skipping to a later paid stage.
    Write-Host ""
    Write-Host ("  ?  {0}" -f $Prompt) -ForegroundColor Yellow
    Write-Host "     [1] Continue" -ForegroundColor Green
    Write-Host "     [2] Skip / End run" -ForegroundColor Yellow
    Write-Host "     [0] Stop" -ForegroundColor DarkGray
    $answer = Read-Host "     Choose 1/2/0"
    if ($null -eq $answer) { return $false }
    if ($answer.Trim() -eq "1") { return $true }
    if ($answer.Trim() -notin @("0", "2")) {
        Write-Host "     Invalid choice; stopping safely." -ForegroundColor Yellow
    }
    return $false
}

if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Detailed
    exit 0
}
if ($AllStages -and $PSBoundParameters.ContainsKey("Step") -and $Step -ne 1) {
    Stop-Workflow "Choose either -AllStages or -Step 0..5, not both."
}
if ($PSBoundParameters.ContainsKey("StartStep") -and -not $AllStages) {
    Stop-Workflow "-StartStep requires -AllStages."
}

$startedAt = Get-Date
Push-Location $PSScriptRoot
try {
    Show-Banner
    Stage "Preflight: Python and Android tools"
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Stop-Workflow "Python not found. Install Python 3.10+ from python.org, reopen PowerShell, then retry."
    }
    $Python = (Get-Command python -ErrorAction Stop).Source
    Run-Command $Python @("--version")

    $adbCommand = Get-Command adb -ErrorAction SilentlyContinue
    $Adb = if ($adbCommand) { $adbCommand.Source } else { "" }
    if (-not $Adb) {
        Note "ADB is not on PATH. Locating an existing ADB or installing platform-tools."
        $Adb = Get-RuntimeValue -LookupArgs @("adb")
    }
    if (-not $Adb) {
        Stop-Workflow "adb.exe was not found. Install Android SDK platform-tools or configure PATH and retry."
    }
    $env:ADB_PATH = $Adb
    Run-Command $Adb @("version")

    Stage "Preflight: Identify Android device"
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
        Note ("Multiple ADB connections: {0}" -f ($online -join ", "))
        Note "Identifying duplicate transports and checking Google One..."
        $candidate = Get-RuntimeValue -LookupArgs @("device")
        if ($candidate -and $online -ccontains $candidate) {
            $Serial = $candidate
            Note ("Auto-selected Android device: {0}" -f $Serial)
        } else {
            Note "Multiple different devices are still eligible; explicit selection is required."
            if (-not $AllStages) {
                Stop-Workflow "Cannot select a single Android device automatically. Rerun with -Serial <exact-adb-serial>; no checkout started."
            }
            for ($i = 0; $i -lt $online.Count; $i++) {
                Note ("[{0}] {1}" -f ($i + 1), $online[$i])
            }
            $deviceAnswer = Read-Host "  Device number (0 to stop)"
            $deviceNumber = 0
            if (-not [int]::TryParse($deviceAnswer, [ref]$deviceNumber) -or
                $deviceNumber -lt 1 -or $deviceNumber -gt $online.Count) {
                Stop-Workflow "Invalid device number; no checkout started."
            }
            $Serial = $online[$deviceNumber - 1]
        }
    }
    Note "Using device: $Serial"
    $AndroidVersion = ((& $Adb -s $Serial shell getprop ro.build.version.release) | Out-String).Trim()
    $AndroidSdk = ((& $Adb -s $Serial shell getprop ro.build.version.sdk) | Out-String).Trim()
    $AndroidAbi = ((& $Adb -s $Serial shell getprop ro.product.cpu.abi) | Out-String).Trim()
    Note ("Android {0} (SDK {1}), ABI {2}, activity lookup {3}" -f $AndroidVersion, $AndroidSdk, $AndroidAbi, $ActivityMethod)

    Stage "Preflight: Verify required Android apps"
    foreach ($package in @("com.android.vending", "com.google.android.apps.subscriptions.red")) {
        $apk = ((& $Adb -s $Serial shell pm path $package) | Out-String).Trim()
        if ($apk -notmatch 'package:') {
            Stop-Workflow ("Android package missing or disabled: {0}. Install/enable it in MuMu." -f $package)
        }
        Note ("Installed: {0}" -f $package)
    }

    Stage "Original Step 0: Environment check"
    Note "The original ultra0.py may repair Frida and change emulator proxy/network settings."
    Run-Command $Python @("ultra0.py", "--check", "--serial", $Serial)

    if ($SetupOnly -or ($Step -eq 0 -and -not $AllStages)) {
        Note "Original Step 0 complete. No checkout or purchase requested."
        return
    }

    Stage "Preflight: Read active Google Play account"
    $playAccount = (Get-RuntimeValue -LookupArgs @("play-account", "--serial", $Serial)).Trim().ToLowerInvariant()
    if ($playAccount) { Note ("Detected Play Store account: {0}" -f $playAccount) }
    else { Write-Warning "Play account not visible yet. Retrying through the Step 1 offer listing." }

    Stage "Original Step 1: List Google AI Pro offers"
    # The script's --list mode only queries product details; it does not call launchBillingFlow.
    Run-Command $Python @("ultra0.py", "--account", "current@device", "--no-add",
                            "--list", "--plan", "pro12", "--serial", $Serial,
                            "--activity-method", $ActivityMethod)
    $offerReport = Read-PythonReport "current"
    if ($offerReport.status -ne "listed") {
        Stop-Workflow ("Offer query did not complete: {0}" -f $offerReport.status)
    }

    # Reuse the Play account that ultra0.py already verified during Step 1.
    # If preflight and listing disagree, abort instead of choosing an account.
    $listedAccount = ""
    if ($offerReport.PSObject.Properties.Name -contains "detected_play_account") {
        $listedAccount = ([string]$offerReport.detected_play_account).Trim().ToLowerInvariant()
    }
    if ($listedAccount -and $listedAccount -notmatch '^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$') {
        Stop-Workflow "Invalid Play Store account returned by Step 1. Verify the Play Store profile."
    }
    if ($playAccount -and $listedAccount -and $playAccount -cne $listedAccount) {
        $accountMismatch = ("Play Store account changed: preflight '{0}', Step 1 '{1}'. " +
                            "Verify the Play Store profile before any checkout.")
        Stop-Workflow ($accountMismatch -f $playAccount, $listedAccount)
    }
    if (-not $playAccount -and $listedAccount) {
        $playAccount = $listedAccount
        Note ("Recovered verified Play Store account from Step 1: {0}" -f $playAccount)
    }
    Note ""
    Note "Returned first pricing phases (NOT proof of eligibility, stacking or future charges):"
    foreach ($offer in @($offerReport.offers)) {
        Note ("  {0,-24} {1,-7} {2}" -f [string]$offer.id, [string]$offer.period, [string]$offer.micros)
    }
    Note "Offer tokens are intentionally not displayed."

    Stage "Diagnostic: Read-only Android Activity inspection"
    $googleOnePid = ((& $Adb -s $Serial shell pidof com.google.android.apps.subscriptions.red) | Out-String).Trim()
    if ($googleOnePid -match '^\d+$') {
        & $Python "scripts/diagnose-activity.py" "--serial" $Serial
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "ActivityThread diagnostic did not pass. This does not prove the chosen lookup method is broken."
        }
    } else {
        Write-Warning "Google One is not running for the optional Activity probe. Open it in MuMu and rerun this check."
    }
    if ($ListOnly -or ($Step -eq 1 -and -not $AllStages)) {
        Note "Original Step 1 complete. No checkout or purchase requested."
        return
    }

    Stage "Optional original Pro subscription steps (2-5)"
    Note "CAUTION: ultra0.py is not a harmless preview. It can automatically press Subscribe."
    Note "An offer with micros=0 may still have later paid phases, and stacking 12+6+6 months is UNVERIFIED."
    if ($AllStages) {
        Note "Choose: 1 = Continue | 2 = Skip | 0 = Stop."
    } else {
        Note "Single-step mode: no console confirmations; the selected step may open and confirm a Google Play checkout."
    }

    # Reuse the selected Play account. No repeated email input is required.
    if (-not $Email -and $playAccount) {
        $Email = $playAccount
        Note ("Using detected Google Play account: {0}" -f $Email)
    }
    if (-not $Email -and $Force) {
        # Mirrors the author's --account current@device --force when profile
        # enumeration is unavailable. No additional account is added.
        $Email = "current@device"
    }
    if (-not $Email) {
        if (-not $AllStages) {
            Stop-Workflow "Cannot identify the active Google Play account. Rerun with -Email <account-email>; no checkout started."
        }
        $Email = Read-Host "Google Play email (Enter to stop)"
    }
    $Email = $Email.Trim().ToLowerInvariant()
    if ($Email -ne "current@device" -and $Email -notmatch '^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$') {
        Note "No valid email supplied; stopping before live billing."
        return
    }
    if ($Force) {
        Write-Warning "--force bypasses only the Play Store account check, NOT Google's eligibility or payment conditions."
        Write-Warning ("Detected Play account: {0}; requested: {1}" -f $playAccount, $Email)
        if ($AllStages) {
            if (-not (Confirm-Exact "Use original --force for this Android account?" "FORCE")) {
                return
            }
        } else {
            Note "The -Force switch was explicitly supplied; no additional console confirmation in single-step mode."
        }
    } elseif (-not $playAccount -or $playAccount -cne $Email) {
        $accountMismatch = ("Play account mismatch or unverified. Detected '{0}', expected '{1}'. " +
                            "Check the Play Store profile before proceeding.")
        Stop-Workflow ($accountMismatch -f $playAccount, $Email)
    }

    # Keep the original author's Pro 5 TB stage numbering and plan IDs.
    # Step 5 is the author's optional additional offer and requires explicit approval.
    $stages = @(
        [pscustomobject]@{ Number = 2; Name = "Pro 12-month offer"; Plan = "pro12"; Offer = "12months-eft"; Stack = $false },
        [pscustomobject]@{ Number = 3; Name = "Pro additional 6 months"; Plan = "pro6"; Offer = "6months-eft"; Stack = $true },
        [pscustomobject]@{ Number = 4; Name = "Pro second additional 6 months"; Plan = "pro6b"; Offer = "6months-eft-2"; Stack = $true },
        [pscustomobject]@{ Number = 5; Name = "Pro optional alternative 6 months"; Plan = "pro6c"; Offer = "6months-eft-ss-2026"; Stack = $true }
    )
    $selectedStages = @(
        if ($AllStages) {
            $stages | Where-Object { $_.Number -ge $StartStep -and $_.Number -le 5 }
        } else {
            $stages | Where-Object { $_.Number -eq $Step }
        }
    )
    if ($AllStages) {
        Note ("The original sequence will start at Step {0} and may initiate real Google Play transactions." -f $StartStep)
        if ($StartStep -gt 2) {
            Note ("Skipping Steps 2-{0}; previous subscription extensions cannot be verified automatically." -f ($StartStep - 1))
            if (-not (Confirm-Exact "Confirm Google Play shows an ACTIVE Google AI Pro subscription and review its next charge date" "ACTIVE")) {
                return
            }
        }
        if (-not (Confirm-Exact ("Run original stages starting at Step {0}, including optional Step 5?" -f $StartStep) "RUN ALL")) {
            return
        }
    }
    $key = $Email.Split('@')[0]
    foreach ($stage in $selectedStages) {
        Stage ("Original Step {0}: {1}" -f $stage.Number, $stage.Name)

        # Recheck offer metadata before each transaction, not just once at
        # the beginning of a potentially long multi-step workflow.
        if ($stage.Number -ne 2 -or $AllStages) {
            Run-Command $Python @("ultra0.py", "--account", "current@device", "--no-add",
                                  "--list", "--plan", $stage.Plan, "--serial", $Serial,
                                  "--activity-method", $ActivityMethod)
            $offerReport = Read-PythonReport "current"
            if ($offerReport.status -ne "listed") {
                Stop-Workflow ("Could not refresh the offer list for Step {0}: {1}" -f $stage.Number, $offerReport.status)
            }
        }
        $available = @($offerReport.offers | Where-Object { $_.id -eq $stage.Offer -and [string]$_.micros -eq "0" })
        if ($available.Count -eq 0) {
            Note ("The expected offer {0} has no zero-priced first phase. Skipping this stage." -f $stage.Offer)
            break
        }

        if ($stage.Stack) {
            Note "The original author requires an existing ACTIVE subscription for an update."
            Note "Do not proceed if the prior subscription was cancelled, expired or not verified."
        } else {
            Note "Step 2 is ONLY for accounts with no active Google One subscription."
            if ($AllStages) {
                if (-not (Confirm-Exact "Confirm Google Play shows NO ACTIVE Google One subscription for this account" "NO ACTIVE")) {
                    Note "Skipping Step 2. For an existing plan, resume with -AllStages -StartStep 3 only after checking Google Play."
                    break
                }
            } else {
                Note "Single-step mode: you selected Step 2 explicitly. Google Play must reject duplicate or ineligible subscriptions."
            }
        }
        Note "Inspect today's checkout price, all future pricing phases and the next charge date."
        Note "A 0-price first phase is NOT proof of free-trial eligibility or stacking."
        # Approve the main sequence once. Step 5 stays optional,
        # and a standalone -Step N run still requires explicit permission.
        if ($AllStages -and $stage.Number -eq 5) {
            if (-not (Confirm-Exact "Run this optional original live stage?" "RUN 5")) { break }
        }

        $args = @("ultra0.py", "--account", $Email, "--no-add", "--no-switch",
                  "--plan", $stage.Plan, "--serial", $Serial, "--activity-method", $ActivityMethod)
        if ($Force) { $args += "--force" }
        if ($stage.Stack) { $args += "--stack" }
        Run-Command $Python $args

        $report = Read-PythonReport $key
        Note ("Python stage status: {0}" -f $report.status)
        if ($report.status -ne "checkout_requested") {
            Note "No verified Subscribe action was recorded; stopping the staged workflow."
            if ($report.PSObject.Properties.Name -contains "sheet" -and $null -ne $report.sheet) {
                if ($report.sheet.PSObject.Properties.Name -contains "reason") {
                    Note ("Checkout reason: {0}" -f $report.sheet.reason)
                }
            }
            if ($report.PSObject.Properties.Name -contains "error") { Note ([string]$report.error) }
            break
        }

        Note "Check Google Play Store > Payments & subscriptions > Subscriptions."
        Note "Confirm the selected Pro plan is ACTIVE and the next charge date moved as expected."
        Note "The original author's 12+6+6+6-month claims are not guaranteed."
        Note "The script's checkout_requested status is NOT proof that a subscription was created."
        if ($AllStages) {
            if (-not (Confirm-Exact "Only if you verified the active plan, renewal date and future price in Google Play, continue?" "VERIFIED")) {
                break
            }
        } else {
            Note "Single step finished. Review the actual subscription and renewal date in Google Play."
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
