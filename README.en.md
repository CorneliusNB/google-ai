# Google AI Pro / Google One Billing Research (English)

[中文说明](README.md) · [Security](SECURITY.md) · [Tests](tests/test_static.py)

## Overview

This repository contains a third-party **experimental** Python tool that connects to an Android device or emulator using ADB and Frida. It queries Google One subscription product offers through Android Play BillingClient APIs and can open the corresponding Google Play checkout screen for **manual review**. The archive was originally distributed with Chinese instructions.

**This is not an official Google project.** The availability of a promotional offer does not prove eligibility, and the code does not guarantee free Google AI Pro, a two-year trial, or that multiple trial periods can be stacked. You must review the actual Google Play price, renewal terms, and subscription status yourself.

**The fixed version does not automatically confirm subscriptions.** It will not press the Subscribe button. Opening a checkout with response code `0` does not mean that the purchase succeeded.

## Source files

| File | Purpose |
|---|---|
| `ultra0.py` | Main ADB + Frida logic, offer query, checkout display, reports |
| `setup_env.py` | Windows environment setup and device diagnostics |
| `query_sku.py` | Read-only SKU/product query |
| `0_环境自检.bat` | Environment diagnostics |
| `1_查看offer列表.bat` | List eligible-looking offers; no checkout |
| `2_Pro_12个月_第1步.bat` | Pro 12-month offer checkout; manual review |
| `3_Pro_加6个月_第2步.bat` | Experimental subscription replacement step |
| `4_Pro_加6个月_第3步.bat` | Another experimental replacement step |
| `5_Pro_备用6个月.bat` | Additional experimental replacement step |
| `使用说明.txt` | Original Chinese instructions (historical claims; not independently verified) |
| `SECURITY.md` | Security caveats and safe operation boundaries |

## Prerequisites

- Windows with Python **3.10 or newer**, Android Platform Tools (`adb`) and an Android emulator/device.
- The original scripts expect a **rooted Android environment** and Google Play + Google One installed. This is sensitive and can violate service/device security boundaries; use only with permission.
- Python dependency: **`frida==16.5.9`** (pinned to match this script's JavaScript bridge assumptions).
- A Google account already signed in to the Play Store on the test device. We recommend **not** putting a password, TOTP seed, or payment-card details in a plaintext accounts file.

No live Google services or device checkout were exercised as part of our static test suite.

## Installation and read-only checks

The repository retains the original Windows installer, which may download tools and configure Frida on the rooted device. Inspect its source before executing it. For manual setup:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
adb devices
python ultra0.py --check
```

If multiple devices are connected, select one explicitly:

```powershell
python ultra0.py --check --serial 127.0.0.1:16384
```

For a **read-only** offer listing (does not open checkout):

```powershell
python ultra0.py --list --plan pro12 --account current@device --no-add
```

`--check` can install/start Frida components on the device. It does **not** alter device network configuration unless you add `--reset-network`. Do not use `--reset-network` casually: it can clear HTTP proxy settings and stop Clash.

## Experimental checkout behavior

The included `.bat` scripts are retained for compatibility, but checkout is **manual confirmation only**. The app requires the currently signed-in Google Play account to be verified; it refuses to skip this check during checkout.

1. Inspect the offers and confirm you are using the intended Play account.
2. If you have an official, eligible offer, the experiment may open the Play checkout screen. **Do not confirm** until you have read the price due now, offer end date, future charges, and renewal/cancellation policy.
3. After any authorized manual purchase, verify the actual subscription status and renewal date directly in Google Play. Never infer success from the script status alone.

**Experimental replacement (`--stack`):** The legacy script attempts to use a current subscription's purchase token and a BillingClient replacement mode. Its claims that 12 + 6 + 6 (+6) months will be stacked are **unverified** and depend on Google's actual eligibility and billing terms. If an active token cannot be verified for the current Play account, the fixed script aborts rather than silently falling back to an ordinary checkout.

## Command-line reference

```text
--check          Run device/Frida diagnostics (may install/start tools)
--list           Query offers, without checkout
--plan pro12     Prefer a named Pro offer; also pro6, pro6b, pro6c
--serial SERIAL  Select an already-connected Android device
--no-add         Don't attempt to sign in an account
--no-switch      Require the currently selected Google Play account
--force          Only allowed with --list (read-only)
--reset-network  Opt in to clearing proxy/stopping selected VPN apps
--stack          Experimental subscription replacement
--old-token      Explicit replacement token, only together with --stack
```

If a checkout is displayed, the script returns the status `checkout_opened_manual_verification_required`. **This does not mean you subscribed.** An offer-listing result may return `list_incomplete` when the backend reports an error.

## Diagnostics

| Symptom | What to check |
|---|---|
| `no device` | Android emulator running, ADB debugging authorized, selected serial |
| Frida connection timeout | Matching versions and architecture of Frida client/server; rooted device permissions |
| No offers shown | The account, product or region might not be eligible; there is no guaranteed fix |
| Cannot verify Play account | Open Play Store, check the signed-in account; do not bypass verification for checkout |
| `matching_active_subscription_not_found` | The Play account, subscription state or database schema couldn't be verified; operation aborted |
| Checkout price is nonzero | Don't approve the purchase unless you consciously accept those charges |
| `checkout_opened_manual_verification_required` | Read checkout details, then verify entitlement and billing date manually |

## Testing

The tests require no Android device, credentials, Frida installation or payment:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q ultra0.py setup_env.py query_sku.py
```

CI runs Python unit checks and validates syntax of the extracted embedded Frida JavaScript with Node.js. These are **static tests only**, not subscription entitlement tests.

## Limitations

- The embedded DEX module is prebuilt and has not been reverse-engineered or fully audited.
- Play Billing internal behavior and eligibility can change without notice.
- UI text parsing is locale-dependent and is not a dependable authorization to spend money.
- Historical source text may describe fully automatic payments or specific durations. These assertions do not apply to the guarded version.
- Reports are local and excluded from Git; treat them as sensitive.

See [Security](SECURITY.md) for additional safeguards.
