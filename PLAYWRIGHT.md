# Playwright on MuMu/Android — English guide

Playwright's Android API is experimental. It communicates with an **existing Android device or emulator through ADB**; it does not implement Google Play BillingClient. The original `ultra0.py` (and Frida) remains responsible for offer-query / checkout logic.

## Installation

1. Start MuMu, enable developer options and ADB, and ensure Play Store and Google One are installed. If Playwright Android cannot see your MuMu instance, connect ADB using the port shown by MuMu, for example `adb connect 127.0.0.1:<YOUR_PORT>`.
2. Install Python 3.10+, compatible Frida and `adb`, then verify `adb devices` shows `device`, not `unauthorized` or `offline`.
3. Install Node.js 22+ and run `npm install` in the repository root. This uses the local `playwright` package; **you do not need to download desktop Chromium** for Playwright's Android device check. Chrome on the Android device is optional unless `--browser-check` is requested.

## Commands

```powershell
# Help (no Android connection required)
node scripts/playwright-android.mjs --help

# Playwright Android preflight (no checkout)
node scripts/playwright-android.mjs doctor

# Pick an ADB serial, if multiple devices are connected
node scripts/playwright-android.mjs doctor --serial 127.0.0.1:16384

# Optional browser smoke check on the Android device
node scripts/playwright-android.mjs doctor --browser-check

# Optional local screenshot; treat the image as confidential
node scripts/playwright-android.mjs doctor --screenshot device-check.png

# Query offers with the original Python source; no checkout
node scripts/playwright-android.mjs offers --plan pro12

# Preview an original checkout command, without Android or Python execution
node scripts/playwright-android.mjs run --step 1 --email your-account@example.com --dry-run
```

To run an **existing** original billing step through the wrapper (not recommended for primary accounts):

```powershell
node scripts/playwright-android.mjs run --step 1 --email your-account@example.com --acknowledge-live-checkout
```

Step 2 (`--step 2`) selects `pro6` and `--stack`; step 3 (`--step 3`) selects `pro6b` and `--stack`. An extra `--step extra` selects `pro6c`. The wrapper requires the actual target email; it **does not** use the original `.bat` files' `--force` account-check bypass. The Python logic itself remains byte-identical to the author's original archive.

**Warning:** The original billing flow may tap Subscribe automatically in the Android application. Only invoke a step when you understand its behavior and accept the terms of any Google Play transaction. No code can promise a zero-cost two-year subscription. The wrapper requires `--acknowledge-live-checkout` to prevent accidental invocation; it does not replace review of Google's checkout conditions.

## Diagnostics and CI

- `doctor` checks the selected Playwright Android device and whether Google Play and Google One packages are installed. It does not log in, change account settings or run checkout.
- `--browser-check` opens a harmless `https://example.com/` page in Chrome on Android; Playwright Android browser support and native Android UI support are experimental and may fail depending on MuMu/Chrome versions.
- `offers` delegates to the unchanged Python code after the device preflight, so Frida may be installed/started and the original environment methods may adjust Android networking.
- CI runs syntax and pure Node tests only; it does not boot a rooted Android emulator. A Windows self-hosted runner with MuMu is required if you want hardware-in-the-loop tests.

Official reference: https://playwright.dev/docs/api/class-android
