# Detailed setup, operations, and troubleshooting

This guide describes the maintained **Python + ADB + Frida** workflow. The Playwright wrapper was removed because it only delegated to the same Python script and added an unnecessary Node.js dependency. The optional **pure JavaScript test** for the Frida hook still uses Node.js in CI; end users do **not** need Node.js.

[Back to README](../README.md) · [Security precautions](../SECURITY.md) · [Original stage reference (English)](ORIGINAL-STEPS.md)

> **Safety:** Offer data and a first pricing phase of 0 do **not** prove that a promotion applies to the account, that the subscription is active, or that time can be stacked. The original `ultra0.py` may automatically click **Subscribe** when not run in `--list` mode. Always inspect Google's live pricing, recurring charges, cancellation terms and actual subscription record in Google Play.

## Prerequisites

- Windows with MuMu, or another Android emulator/device that supports debugging, root and a compatible Frida server.
- Python 3.10+; Android SDK platform-tools or a working ADB path.
- Google Play Store and Google One installed and usable on the Android device.
- Frida 16.5.9 is pinned by this repository's current implementation, not guaranteed compatible with every Android/ART build.
- Account signed into Google Play Store; check the active profile carefully.

The original helper `setup_env.py` can install Frida and ADB and attempt to connect emulator endpoints. Review its source first: setup and runtime checks may install/replace dependencies or change Android proxy/network settings.

## Quick start

Clone the repository if needed, or update it:

```powershell
git clone https://github.com/hoangsvit/google-ai.git
cd google-ai
git pull --ff-only
```

### Install ADB first (Windows PowerShell)

Run the setup helper from the repository directory:

```powershell
python --version
python setup_env.py
```

The helper searches `ADB_PATH`, existing `platform-tools` folders, known MuMu locations, and PATH. It verifies `adb.exe version` works. If it needs to download Google's official Platform-Tools, it extracts them in a fresh temporary directory and installs into the project or, if that directory is locked, `%LOCALAPPDATA%\google-ai\platform-tools`.

**If `adb` is not recognized in PowerShell:** You can use `.\\run-all.ps1 -Serial emulator-5554 -ListOnly` without changing PATH. Or run the local executable:

```powershell
.\\platform-tools\\adb.exe version
.\\platform-tools\\adb.exe devices
```

For a per-user installation, use `& "$env:LOCALAPPDATA\\google-ai\\platform-tools\\adb.exe" devices`.

**If PowerShell reports an inline Python syntax error or `UnicodeEncodeError: cp1252`:** Old versions passed inline `python -c` code through PowerShell and could corrupt Python quoting, then try to print Unicode status symbols using the wrong Windows codepage. Run `git pull --ff-only`. The updated `run-all.ps1` uses `scripts/runtime-lookup.py` to return only Base64-encoded UTF-8 values in ASCII, preventing this issue without changing Windows codepages.

**If `setup_env.py` previously raised `PermissionError: [Errno 13] ... platform-tools\\adb.exe`:** The file may be locked by an emulator/ADB process or protected by directory permissions. Update the repository with `git pull --ff-only` and rerun setup. The installer now avoids overwriting working ADB files and falls back to the per-user directory if the project folder cannot be updated. Do not force-delete the file or disable antivirus.

Then inspect the device:

```powershell
adb devices
adb -s emulator-5554 shell getprop ro.build.version.release
adb -s emulator-5554 shell getprop ro.build.version.sdk
adb -s emulator-5554 shell getprop ro.product.cpu.abi
```

Replace `emulator-5554` with the serial from `adb devices`. If no device is online, start MuMu, enable ADB debugging, approve device authorization and use the ADB endpoint documented by your emulator. Do not assume a universal port number. A device in `offline` or `unauthorized` state is not ready.

**One command for setup and diagnostics (automatic device selection):**

```powershell
.\run-all.ps1 -ListOnly
```

If `adb devices` lists several connections such as `127.0.0.1:16384`, `127.0.0.1:7555`, and `emulator-5554`, these may all point to the same Android instance. The tool checks each instance's boot UUID and treats matching UUIDs as aliases. If several different Android kernels are connected, it selects the one uniquely running Google One or the only one with Google One installed. It does **not** guess if the identification is inconclusive: specify `-Serial emulator-5554` or answer the prompt only in that case.

For setup only:

```powershell
.\run-all.ps1 -SetupOnly
```

For explicit guided checkout (can result in a real purchase):

```powershell
.\run-all.ps1 -Serial emulator-5554 -Email your-email@gmail.com
```

The guided script checks the selected device and Google Play account, displays the offers and requires a specific confirmation before each live stage. It pauses between stages for manual verification. The original Python program can still press Subscribe automatically during a live stage; **this is not a simulation**.

If local execution policy prevents PowerShell scripts, review the file and follow your organization's Windows execution-policy rules rather than disabling system protections globally.

## Direct Python and diagnostic commands

Environment check:

```powershell
python ultra0.py --check --serial emulator-5554
```

**Offer listing without checkout:**

```powershell
python ultra0.py --account "current@device" --no-add --list --plan pro12 --serial emulator-5554
```

In listing mode, the email placeholder identifies the device's current account and is **not proof that the account matches any intended email**. Check Google Play's profile in the emulator.

Read-only Activity inspection, after opening Google One in the emulator:

```powershell
python scripts/diagnose-activity.py --serial emulator-5554
```

The tool reports `ok` only when it can read a usable Android Activity through `ActivityThread`. It does not query or confirm a purchase.

## Android and Frida compatibility

The default Android Activity strategy is `--activity-method auto`: try `Java.choose()`, then fallback to `ActivityThread.mActivities`. Force one method for diagnostics with:

```powershell
python ultra0.py --check --serial emulator-5554
python scripts/diagnose-activity.py --serial emulator-5554
```

The guided PowerShell script accepts `-ActivityMethod auto|choose|thread`, and the Python CLI accepts `--activity-method auto|choose|thread`. A successful read-only Activity probe is not proof that checkout will work.

On some Android 15 / API 35 x86_64 emulator builds, Frida `Java.choose()` raises a `libart.so` / `EnsurePluginLoaded` error. This is a runtime compatibility issue distinct from Google Play account eligibility. The fallback may help, but is not guaranteed across Android vendors and versions.

## Original stage mapping (reference only)

| Stage | Original shortcut | Python option |
| --- | --- | --- |
| Claimed 12-month offer | `02-pro-12-months.bat` | `--plan pro12` |
| Claimed additional six months | `03-pro-add-6-months.bat` | `--plan pro6 --stack` |
| Claimed additional six months | `04-pro-add-6-months-again.bat` | `--plan pro6b --stack` |
| Optional alternative six months | `05-pro-alternative-6-months.bat` | `--plan pro6c --stack` |

The legacy-compatible `.bat` files use `--force` to bypass account verification and may initiate purchase flows. They remain available to preserve the original author's files, but the safer guided PowerShell entrypoint uses `--no-switch` and checks account identity. The original 12+6+6 stacking claim is unverified and cannot be inferred from offer identifiers.

## Common failures

| Result | Meaning / next step |
| --- | --- |
| `account_unverified` | Script cannot read active Google Play email; open the Store profile and check account manually |
| `wrong_account` | Account read from Google Play differs from the target; do not bypass it |
| `app_not_started` | Google One package/process did not start; open app manually and inspect ADB process |
| `activity_lookup_failed` | Frida could not locate a usable Activity; check ART/Frida compatibility and read-only probe |
| `no_activity` | Running app has no usable Activity; return to a foreground Google One screen |
| `billing_flow_error` | BillingClient returned an error; read sanitized `launched` and `errors` fields |
| `launch_failed` | Script did not observe successful checkout launch; does not imply a purchase |
| `listed` | Offer details returned, but no checkout or subscription confirmed |

For local status without exposing offer tokens, select only fields from the report:

```powershell
Get-Content .\ultra0-report\eplusdotdev.json -Raw |
    ConvertFrom-Json |
    Select-Object status, error, launched, errors
```

Do **not** publish full JSON reports, offer tokens, purchase tokens, passwords, 2FA secrets or card data. The repository ignores common sensitive local files.

If a checkout is ever initiated, confirm subscription status, renewal date, amount and currency directly in **Google Play Store → Payments & subscriptions → Subscriptions**. A message saying a checkout window opened does not prove that any subscription was activated.

## Project files

- `ultra0.py`: Python entrypoint and original billing orchestration.
- `run-all.ps1`: Guided Windows workflow with safety checks.
- `setup_env.py`: Original setup helper.
- `query_sku.py`: Direct product/offer query helper.
- `assets/frida/billing.js`: Extracted Frida hook.
- `assets/modules/module_521.b64`: Original embedded DEX archive as Base64.
- `scripts/diagnose-activity.py`: Read-only ActivityThread probe.
- `scripts/runtime-lookup.py`: ASCII-safe runtime discovery for Windows PowerShell.
- `tests/`: Python tests and one dependency-free Node.js Frida JavaScript test.
- `.github/workflows/static-checks.yml`: Hosted CI; **no actual Android billing test**.
