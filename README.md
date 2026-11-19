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

3. If PowerShell reports **`adb : The term 'adb' is not recognized`**, ADB exists but may not be in PATH. Enable the detected installation **in the current PowerShell session only**:

```powershell
$adbPath = (python -c 'import setup_env; print(setup_env.find_adb())' | Select-Object -Last 1).Trim()
$env:Path = "$(Split-Path -Parent $adbPath);$env:Path"
adb version
adb devices
```

   Alternatively use `& $adbPath devices` without changing PATH. Administrator permissions are not required for the temporary PATH change.

4. Use the serial shown by `adb devices` (for example, `emulator-5554`) to run the **read-only workflow**:

```powershell
.\run-all.ps1 -Serial emulator-5554 -ListOnly
```

**Windows `PermissionError: [Errno 13] ... platform-tools\\adb.exe`:** If ADB is in use or the project directory is not writable, the updated installer reuses a working copy or extracts new files into a temporary folder and installs them under `%LOCALAPPDATA%\google-ai\platform-tools`. Run `git pull --ff-only` and retry `python setup_env.py`. Do not force-delete a running ADB executable or disable antivirus. Manual installation into a writable directory is also supported by setting `$env:ADB_PATH` to the complete path to `adb.exe`.

For environment setup only:

```powershell
.\run-all.ps1 -Serial emulator-5554 -SetupOnly
```

For **interactive** stages that can open Google Play checkout (only after reviewing the original source and the Play Store terms):

```powershell
.\run-all.ps1 -Serial emulator-5554 -Email your-email@gmail.com
```

The guided script requires explicit confirmation for each live stage, validates the selected Play account, and halts between stages for subscription verification. It never uses `--force`. A CI pass **does not** prove real billing compatibility with your device.

## Project layout

```text
google-ai/
├── ultra0.py                      # Original Python CLI / device and billing orchestration
├── run-all.ps1                    # Guided Windows entry point
├── setup_env.py                   # Original environment installer
├── query_sku.py                   # Product/offer query CLI
├── requirements.txt               # Pinned Frida dependency
├── assets/
│   ├── frida/billing.js           # Android Java/BillingClient Frida hook
│   └── modules/module_521.b64     # Bundled original DEX package (Base64)
├── scripts/
│   └── diagnose-activity.py       # Read-only ActivityThread diagnostic
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

The default Activity lookup is `auto` (Frida `Java.choose` followed by `ActivityThread`). The optional `--activity-method choose|thread` forces a lookup strategy. If both fail, the script stops instead of guessing.

## Development and tests

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
node --test tests/test_activity_lookup.test.mjs
```

The GitHub workflow validates Python syntax, verifies the bundled assets, tests Activity fallback behavior (including a dependency-free Node.js test), and checks Windows PowerShell syntax. No real Google subscription is created in CI.

**Do not commit** account files, passwords, 2FA seeds, payment details, Play offer tokens or local report JSON. Read [SECURITY.md](SECURITY.md) before running a live billing stage.
