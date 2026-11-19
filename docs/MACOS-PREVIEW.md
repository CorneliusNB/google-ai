# macOS preview: Android diagnostics only

Status: development preview. No real Mac/MuMu hardware has been tested.
This is not a supported macOS release or a guarantee of subscription eligibility.

## Scope

The native launcher and macOS adapter expose only Step 0 (Android environment)
and Step 1 (Google Play offer metadata). Checkout Steps 2–5, subscription
sequences and automatic Subscribe actions are blocked on macOS. The existing
Windows PowerShell and Billing engine are not changed.

## Requirements

- macOS with Python 3.10+.
- Android SDK Platform-Tools with adb on PATH. On a Mac with Homebrew:
    brew install android-platform-tools
- An Android device/emulator that supports root, ADB, Google Play Store
  and Google One. MuMuPlayer Pro for Mac supports Apple Silicon, not Intel.
- The launcher creates a local .venv and installs Textual and Frida 16.5.9.
  It does not install the emulator, or ADB. Frida server support on rooted
  Android devices has not been validated.

## Commands (run from repository root)

    sh run-macos.sh --help
    adb devices
    sh run-macos.sh             # Textual dashboard, Steps 0 and 1 only
    sh run-macos.sh --check     # Environment preflight, may change settings
    sh run-macos.sh --list      # Offer listing, no subscription checkout

Do not run ultra0.py directly with billing flags on Mac. Do not use
Windows-only setup_env.py as the Mac installer.

## Important side effects

Neither supported mode opens checkout, but Android diagnostics may download
or restart Frida, push local modules, start apps and modify proxy/network
settings. Only run on an Android device you own or are authorized to inspect.
Do not post payment data, account emails, purchase tokens or raw logs.

## Validation limits

GitHub Actions tests the Python bridge, shell syntax, pinned Frida install
and Textual checkout guards on macos-15 (Apple Silicon) and macos-15-intel.
CI does not contain a rooted emulator, a real Play Store account, or MuMu.
No paid checkout runs in CI. Real-device validation is still required before
claiming compatibility or publishing a macOS release.
