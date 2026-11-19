# Google AI — Android / MuMu Toolkit

A Windows toolkit for inspecting Google AI Pro offers through Google One, ADB and Frida. It preserves the original author's step-by-step workflow and includes fixes for MuMu/Android compatibility.

> **Billing warning:** Steps 2–5 can open Google Play checkout and automatically tap **Subscribe**. An offer with a first phase priced at 0 is **not** proof of eligibility, a free subscription, or an extended renewal date. Always verify the terms and subscription in Google Play.

## Requirements

- Windows with PowerShell 5.1+, Python 3.10+, and a running rooted MuMu emulator with ADB enabled.
- Google Play Store and Google One installed; sign in to the intended Google account.
- For a checkout stage, prepare a valid payment method in Google Play. The script does not make trial eligibility guarantees.

## Quick start

Run from the repository directory:

```powershell
git pull --ff-only
python setup_env.py
.\run-all.ps1 -Step 1
```

The setup helper locates or installs ADB, configures Frida 16.5.9 and checks MuMu. Step 1 lists offers **without purchasing**. An unambiguous Android device and the active Play Store email are detected automatically; you usually do not need `-Serial` or `-Email`.

### Run the author's full sequence

```powershell
.\run-all.ps1 -AllStages
```

This runs the environment check, offer listing, and the original Pro stages **2 → 3 → 4**, then offers optional **Step 5**. Type `RUN ALL` once to start, then `VERIFIED` only after checking each attempted transaction in Google Play. Step 5 requires a separate `RUN 5` approval; otherwise it is skipped. Stopping at any prompt prevents subsequent stages.

### Run one step

| Step | Action | Command |
| --- | --- | --- |
| 0 | Environment check | `.\run-all.ps1 -Step 0` |
| 1 | List Pro offers (read-only) | `.\run-all.ps1 -Step 1` |
| 2 | Original 12-month offer (`pro12`) | `.\run-all.ps1 -Step 2` |
| 3 | Original +6-month update (`pro6 --stack`) | `.\run-all.ps1 -Step 3` |
| 4 | Original second +6-month update (`pro6b --stack`) | `.\run-all.ps1 -Step 4` |
| 5 | Optional +6-month offer (`pro6c --stack`) | `.\run-all.ps1 -Step 5` |

Running a single checkout step requires `RUN N` (for example `RUN 2`), and the script requests subscription verification afterward. The default `.\run-all.ps1` is Step 1 (read-only).

### Optional arguments

```powershell
.\run-all.ps1 -AllStages -Email "account@gmail.com"   # Require this Play account
.\run-all.ps1 -Step 1 -Serial emulator-5554           # Choose an ADB connection
.\run-all.ps1 -AllStages -Force                        # Bypass account verification
```

`-Force` mirrors the author's `--force` **only for the Play account check** and asks for an additional `FORCE` confirmation. It does not override Google Play eligibility, prices or subscription-update checks. Avoid it when the account is already detected.

## Results and documentation

Read-only offers and stage diagnostics are saved under `ultra0-report/`. A status such as `checkout_requested` is **not** confirmation of an active subscription. Check the real plan, charge, currency and renewal date at [Google Play Subscriptions](https://play.google.com/store/account/subscriptions).

- [Detailed setup and troubleshooting](docs/DETAILED-GUIDE.md)
- [Original author's steps and batch-file mapping](docs/ORIGINAL-STEPS.md)
- [Historical author notes](docs/AUTHOR-NOTES.md)
- [Security and billing precautions](SECURITY.md)

The project's GitHub Actions test Python, PowerShell, and mocked Frida/Billing behavior. They do **not** perform real Google Play transactions.
