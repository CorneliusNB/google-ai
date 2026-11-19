# Windows + MuMu pre-release smoke test (manual)

This is the hardware validation checklist for **ePlus AI Toolkit v1.0.1**. GitHub Actions cannot perform it because CI does not have a rooted MuMu/Android instance or a real Google Play account. **Do not test billing Steps 2–5** for release verification.

## Before starting

- Windows 10/11 with PowerShell 5.1 or later, Python 3.10+, and the toolkit extracted into a separate folder.
- MuMuPlayer installed from [the official download](https://www.mumuplayer.com/download/), started with Android root and ADB available, and Google Play Store / Google One installed.
- Only a device and account that you control or have permission to administer.
- Have no payment checkout pending. Back up emulator data before Step 0: environment preparation can modify local ADB/Frida/emulator/proxy settings.
- Never include passwords, OTPs, full emails, purchase tokens, raw logs or payment details in screenshots/issues.

## Checks (no subscription checkout)

| Check | Action | Pass criteria |
| --- | --- | --- |
| A. Launcher help | In PowerShell, run the launcher help command below | Help text renders without Unicode error or attempting any checkout |
| B. Device detection | Run ADB listing below if ADB is available | Intended Android serial appears as device (not offline or unauthorized) |
| C. Dashboard | Run no-argument launcher | Textual dashboard shows Check Device & Offers, Live Status and expandable advanced controls, without starting a paid stage |
| D. Read-only offers | Press Check Device & Offers or run Step 1 from the CLI | Status shows the checked Android/account; result may be offers, empty or an explanatory failure—never a payment checkout |
| E. Details, Stop and Exit | Inspect technical details and use Stop on a safe diagnostic if applicable | No stale previous-account status, logs remain readable, and Exit works without launching another Step |
| F. Source ZIP | Extract the published GitHub Source code ZIP into another folder | Required scripts and assets are present; launcher help works from the extracted copy |

Launcher's help and read-only check:

    .\run-all.ps1 -Help
    adb devices
    .\run-all.ps1
    .\run-all.ps1 -Step 1 -Debug

Use Step 0 diagnostics *only if needed*, because they can install or repair ADB/Frida and modify Android settings:

    .\run-all.ps1 -Step 0

A missing offer or an ineligible account is **not by itself a toolkit failure**; capture a sanitized diagnostic summary. Do not turn a failure into a success by using Force or bypassing account matching. No paid checkout should be attempted by this procedure.

## Evidence to record

- Windows version, PowerShell version, Python version
- MuMuPlayer / Android version and ADB device state (mask unique serials if necessary)
- Date and Git commit or release tag tested
- Results A–F with pass / fail / not tested, plus sanitized error type if failing
- An explicit statement: **No live Google Play checkout was executed**

Only mark real-device validation complete if A–F have been run with no unexplained blockers. CI passing by itself is **not sufficient**.

## Publishing after checks pass

Once this checklist has actually passed and the release preparation PR has been merged to main:

1. Confirm the **Static checks** workflow for the latest main commit is green.
2. Open [GitHub Actions](https://github.com/hoangsvit/google-ai/actions), select **Publish ePlus AI Toolkit v1.0.1 (manual)**, then choose **Run workflow** on **main**.
3. Enable **I completed docs/WINDOWS-SMOKE-TEST.md on real Windows + MuMu** only if you have verified those checks.
4. The workflow independently reruns Windows smoke tests, checks the exact main commit's Static checks, then creates the **1.0.1** release and GitHub-generated source archives. It will not overwrite an existing tag or release.

No repository code is released merely by opening or merging a documentation PR. Publishing is an explicit action, and it does not bundle MuMuPlayer or produce a Windows installer.

See [release notes](releases/v1.0.1.md), [README](../README.md) and [Security](../SECURITY.md).
