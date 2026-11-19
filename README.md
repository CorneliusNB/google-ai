# Google AI — Android / MuMu Toolkit

Python + ADB + Frida utilities for inspecting Google Play promotional offers, diagnosing Android compatibility, and optionally running the original author's subscription flow. **Playwright is not required or installed.**

**Documentation:** [Detailed setup and troubleshooting](docs/DETAILED-GUIDE.md) · [Historical author notes (English)](docs/AUTHOR-NOTES.md) · [Original step reference (English)](docs/ORIGINAL-STEPS.md) · [Security](SECURITY.md)

> **Important:** Offer discovery is not subscription eligibility. The original billing code can automatically press Subscribe and charge a payment method. Google determines actual pricing, free periods and renewal dates; the 12 + 6 + 6 month stacking claim has **not** been independently verified. Prefer read-only commands first.

## Quick start (Windows / PowerShell)

1. Install **Python 3.10+** and start MuMu with ADB debugging enabled. Sign in to the Google Play account you intend to inspect.
2. In the repository folder, update and run the environment installer **before using `adb`**:

```powershell
git pull --ff-only
python --version
python setup_env.py
```

   The installer looks for a working ADB in MuMu, PATH, the repository or your user profile. It downloads [official Android SDK Platform-Tools](https://developer.android.com/tools/releases/platform-tools) only when needed. It also checks Frida/root and may change emulator network settings; review the setup script first.

3. If PowerShell reports **`adb : The term 'adb' is not recognized`**, ADB is not on PATH. **The guided `run-all.ps1` script finds ADB automatically**, so changing PATH is optional.

   To test the local installation directly:

```powershell
.\\platform-tools\\adb.exe version
.\\platform-tools\\adb.exe devices
```

   If Platform-Tools was installed in the user fallback directory, run `& "$env:LOCALAPPDATA\\google-ai\\platform-tools\\adb.exe" devices` instead.

   Older versions of `run-all.ps1` could break `python -c` quoting and raise `UnicodeEncodeError: cp1252`. The current version calls `scripts/runtime-lookup.py` for machine-readable ADB and Google Play account discovery, avoiding both issues.

4. Run the **read-only workflow** without choosing a serial manually:

```powershell
.\run-all.ps1 -ListOnly
```

   The script checks whether the ADB transports belong to the same Android device using its kernel boot UUID. If several distinct Android devices are connected, it can automatically select the only one running Google One (or the only one with Google One installed). **It asks you to enter a serial only if the selection remains ambiguous.** You can always override the selection with `-Serial emulator-5554`.

**Windows `PermissionError: [Errno 13] ... platform-tools\\adb.exe`:** If ADB is in use or the project directory is not writable, the updated installer reuses a working copy or extracts new files into a temporary folder and installs them under `%LOCALAPPDATA%\google-ai\platform-tools`. Run `git pull --ff-only` and retry `python setup_env.py`. Do not force-delete a running ADB executable or disable antivirus. Manual installation into a writable directory is also supported by setting `$env:ADB_PATH` to the complete path to `adb.exe`.

For environment setup only:

```powershell
.\run-all.ps1 -SetupOnly
```

For the author's **interactive main stages 2–4** (possible real checkout after explicit confirmation):

```powershell
.\run-all.ps1 -AllStages -Email your-email@gmail.com
```

The guided script requires explicit confirmation for each live stage, validates the selected Play account, and halts between stages for subscription verification. It never uses `--force`. A CI pass **does not** prove real billing compatibility with your device.

## Step-by-step workflow: original author's Google AI Pro (5 TB) flow

The **Step numbers below match the author's MuMu guide and batch scripts**. Environment checks and device/account discovery are preflight operations, not extra subscription stages.

| Original Step | What it does | Command | Checkout |
| --- | --- | --- | --- |
| **0 — Environment check** | Verify Python, ADB, root, Frida, Google Play and Google One | `.\run-all.ps1 -Step 0` | No |
| **1 — List offers** | Query current Google AI Pro offer metadata | `.\run-all.ps1 -Step 1` | No |
| **2 — Pro 12-month offer** | Original plan `pro12`, offer `12months-eft` | `.\run-all.ps1 -Step 2 -Email "account@gmail.com"` | Possible real purchase |
| **3 — Additional 6 months** | Original `pro6 --stack`, offer `6months-eft` | `.\run-all.ps1 -Step 3 -Email "account@gmail.com"` | Possible real purchase |
| **4 — Second additional 6 months** | Original `pro6b --stack`, offer `6months-eft-2` | `.\run-all.ps1 -Step 4 -Email "account@gmail.com"` | Possible real purchase |
| **5 — Optional alternative 6 months** | Original `pro6c --stack`, offer `6months-eft-ss-2026` | `.\run-all.ps1 -Step 5 -Email "account@gmail.com"` | Possible real purchase |

Install tools once and inspect offers before attempting a billing stage:

```powershell
git pull --ff-only
python setup_env.py
.\run-all.ps1 -Step 0
.\run-all.ps1 -Step 1
```

To run the **author's main sequence (Steps 2–4)** in one guided session, use:

```powershell
.\run-all.ps1 -AllStages -Email "account@gmail.com"
```

This guided sequence **excludes optional Step 5**. Each billing step requires you to type `RUN 2` / `I ACCEPT 2` (or the matching step number) and then `VERIFIED` only after checking the real active plan, next charge date and price in Google Play. If any offer, activity lookup, account check, or token validation fails, stop; do not bypass it with `--force`.

The default `.\run-all.ps1` is equivalent to **Step 1** (read-only). The previous `-SetupOnly` and `-ListOnly` switches remain aliases for environment-only and offer-only workflows. Auto device detection remains enabled; you can specify `-Serial emulator-5554` when needed.

**Important:** These are the original author's claimed offer periods, not verified Google entitlements. Google Play may reject offers, charge money, or calculate different renewal dates. Merely opening checkout or receiving a 0-priced first phase does not prove a subscription or an extension succeeded.

## Project layout

```text
google-ai/
├── ultra0.py                      # Original Python CLI / device and billing orchestration
├── run-all.ps1                    # Guided Windows entry point
├── setup_env.py                   # Original environment installer
├── device_selector.py             # Detect duplicate ADB transports and choose safely
├── query_sku.py                   # Product/offer query CLI
├── requirements.txt               # Pinned Frida dependency
├── assets/
│   ├── frida/billing.js           # Android Java/BillingClient Frida hook
│   └── modules/module_521.b64     # Bundled original DEX package (Base64)
├── scripts/
│   ├── diagnose-activity.py       # Read-only ActivityThread diagnostic
│   └── runtime-lookup.py          # ASCII-safe Windows ADB and account lookup
├── tests/                         # Python unit tests + pure Node.js Frida-JS tests, no live purchases
├── docs/DETAILED-GUIDE.md         # Comprehensive usage and troubleshooting
├── .github/workflows/             # CI syntax + simulated tests
└── *.bat                          # Preserved original Windows shortcuts
```

All original root commands remain supported, including `python ultra0.py --check`, `python query_sku.py`, `python setup_env.py`, `.\run-all.ps1` and the legacy batch files. The two extracted assets are loaded **relative to `ultra0.py`**, so running commands from other working directories does not depend on the shell location.

## Direct Python commands

```powershell
python ultra0.py --check --serial emulator-5554
python ultra0.py --account "current@device" --no-add --list --plan pro12 --serial emulator-5554
python scripts/diagnose-activity.py --serial emulator-5554
```

On Android 15, Frida may fail to enumerate a running process by PID. The tool now verifies the package PID through ADB on the selected serial and does not require Frida `get_process()` to succeed. If the process changes or belongs to another package, attachment is rejected. This check is independent of the Activity lookup.

The default Activity lookup is `auto` (Frida `Java.choose` followed by `ActivityThread`). The optional `--activity-method choose|thread` forces a lookup strategy. If both fail, the script stops instead of guessing.

## Development and tests

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
node --test tests/test_activity_lookup.test.mjs
```

The GitHub workflow validates Python syntax, verifies the bundled assets, tests Activity fallback behavior (including a dependency-free Node.js test), and checks Windows PowerShell syntax. No real Google subscription is created in CI.

**Do not commit** account files, passwords, 2FA seeds, payment details, Play offer tokens or local report JSON. Read [SECURITY.md](SECURITY.md) before running a live billing stage.
