# Google AI Pro — Android / MuMu Python and Playwright guide

**English is the default documentation language.** [中文说明 (Chinese)](README.zh-CN.md) · [Original author's instructions (Chinese)](使用说明.txt) · [Playwright details](PLAYWRIGHT.md) · [Security notes](SECURITY.md)

This repository contains the **original author's Python + ADB + Frida implementation** and an **optional Playwright Android wrapper**. The original Python billing code and Windows batch-file behavior are preserved. The wrapper launches the Python commands; it does **not** replace Google Play BillingClient with a web browser.

> **Read before running:** The author's 12 + 6 + 6-month Google AI Pro offer/stacking claim is **unverified**. Google decides offer eligibility, price, renewal date, and subscription status. The original script uses `--force` to skip its account-check guard and may **automatically tap Subscribe**. A displayed zero price is not proof of free service or a completed purchase. Review the account, all charges and renewal terms in Google Play. Do not run this with your primary account or store login/password/2FA/payment-card details in plaintext.

## 1. Prerequisites

- **Windows** with [MuMu Android emulator](https://www.mumuplayer.com/) or another compatible rooted Android device/emulator.
- Enable **root** and **ADB debugging** in your emulator's settings; restart the emulator if required. Use only devices and accounts you control.
- Install Google Play Store and the **Google One** Android app; sign in to the intended Google account in Play Store.
- **Python 3.10+**, with `python` accessible from PowerShell.
- **Node.js 22+** if you want the optional Playwright wrapper. Android Playwright support is experimental.
- ADB access to the emulator/device. The original Windows setup script helps locate/install ADB and **Frida 16.5.9**.

**GitHub Actions hosted runners cannot substitute for a rooted MuMu instance with the Google One app.** CI in this repo tests syntax/command mappings only; it does not run a real purchase.

## 2. Get the project

Open **PowerShell** on your Windows PC:

```powershell
git clone https://github.com/hoangsvit/google-ai.git
cd google-ai
python --version
```

This repository is private; clone using a GitHub account with access.

## 3. Set up MuMu, ADB, and Python/Frida (once)

1. Start MuMu and enable **root** and **ADB debugging** in its developer/emulator settings.
2. Confirm Play Store and Google One are installed, and check the account shown in Play Store.
3. In the repository folder, run **`一键安装环境.bat`** (double-click in File Explorer). This calls the original `setup_env.py`, checks Python, sets up Frida and ADB, and attempts to connect/self-check the emulator. **Inspect the batch/Python source before running**: it installs tools and may change emulator networking.
4. Run **`0_环境自检.bat`** (or the matching Python check below). Don't proceed if the check fails.

```powershell
adb devices
python ultra0.py --check
```

`adb devices` should show a device with status **`device`**, not `offline` or `unauthorized`. If none appears, connect to the ADB endpoint configured by **your MuMu installation** and check again:

```powershell
adb connect 127.0.0.1:<YOUR_MUMU_ADB_PORT>
adb devices
```

The above is a placeholder, not a universal MuMu port. If more than one device is connected, pass `--serial` to the Playwright runner.

## 4. Inspect available offers without opening checkout

**Python / original batch file:**

```powershell
# Or double-click: 1_查看offer列表.bat
python ultra0.py --account "current@device" --no-add --force --list --plan pro12
```

**Playwright wrapper:**

```powershell
npm install
npm run android:doctor
npm run android:offers
# Or query a specific offer:
node scripts/playwright-android.mjs offers --plan pro6
```

The Playwright `doctor` command verifies that a reachable Android device has Play Store and Google One installed. The `offers` command performs the device check then delegates to the **original Python/Frida script**; it can still start Frida and alter Android networking. No checkout is requested in listing mode.

## 5. Original three-step commands vs. Playwright

The following are the **original author's claimed** subscription stages. They are reproduced here to document the existing code, **not as a promise** that a free trial or stacked subscription will be granted.

| Stage | Original Windows batch file | Python plan | Playwright dry-run |
| --- | --- | --- | --- |
| 1 — claimed 12 months | `2_Pro_12个月_第1步.bat` | `pro12` | `--step 1` |
| 2 — claimed +6 months | `3_Pro_加6个月_第2步.bat` | `pro6` with `--stack` | `--step 2` |
| 3 — claimed +6 months | `4_Pro_加6个月_第3步.bat` | `pro6b` with `--stack` | `--step 3` |
| Optional extra | `5_Pro_备用6个月.bat` | `pro6c` with `--stack` | `--step extra` |

### Inspect the commands safely (no Android or purchase)

```powershell
node scripts/playwright-android.mjs run --step 1 --dry-run
node scripts/playwright-android.mjs run --step 2 --dry-run
node scripts/playwright-android.mjs run --step 3 --dry-run
```

The corresponding original Python arguments are:

```powershell
# Step 1
python ultra0.py --account "current@device" --no-add --force --plan pro12

# Step 2
python ultra0.py --account "current@device" --no-add --force --stack --plan pro6

# Step 3
python ultra0.py --account "current@device" --no-add --force --stack --plan pro6b

# Optional extra
python ultra0.py --account "current@device" --no-add --force --stack --plan pro6c
```

**Important:** These Python commands and original `.bat` files enter the author's **live checkout flow**, which can automatically confirm a purchase. `--force` bypasses the script's account-match check; it does **not** guarantee that Google accepts an offer. Never rely only on the script's status message to decide that a subscription is active.

### Running an existing stage through Playwright

The optional wrapper requires an explicit acknowledgement to invoke a live checkout:

```powershell
# Example: invoke the original first-stage Python logic (live billing flow)
node scripts/playwright-android.mjs run --step 1 --acknowledge-live-checkout

# Optional: specify the intended account string / device
node scripts/playwright-android.mjs run --step 1 --email address@example.com --serial <ADB_SERIAL> --acknowledge-live-checkout
```

Replace placeholders with actual values. The same structure applies to `--step 2` and `--step 3`. Playwright checks the device, then calls the **unmodified original `ultra0.py`** with the corresponding arguments. There is no Playwright-only/browser-only subscription flow.

**After any checkout**, verify your actual Google Play subscription status, next charge date, currency, renewal amount, and any cancellation terms independently in **Play Store → Profile → Payments & subscriptions → Subscriptions**. Do not assume success because a billing window appeared. A change to the renewal date is not independently verified by the repository's tests.

## 6. Troubleshooting

| Symptom | Check |
| --- | --- |
| `adb` not recognized | Install Android SDK platform-tools or use the original environment setup script; reopen the shell |
| No Android device in `adb devices` | Start MuMu, enable ADB debugging, check MuMu's documented ADB endpoint, reconnect |
| `unauthorized` / `offline` | Approve the debugging prompt, restart ADB/MuMu, confirm emulator settings |
| More than one device | Add `--serial <ADB_SERIAL>` to the Playwright command |
| `No Android device found` in Playwright | Ensure `adb devices` works first; check installed `playwright` and emulator compatibility |
| Google Play / Google One package not found | Install or enable the missing app in the emulator |
| Frida missing or version mismatch | Run the original environment setup; it is designed for Frida **16.5.9**, not an untested major release |
| Play Store cannot connect | Confirm Android internet access, account sign-in and network settings; the original check can modify proxy settings |
| Billing screen says ineligible or displays a price | **Do not confirm** the transaction; Google determines eligibility and the payable amount |
| Checkout opened but status is uncertain | Check the subscription directly in Google Play; don't infer success from a launched activity |

## 7. Repository files

| Path | Purpose |
| --- | --- |
| `ultra0.py` | Original Python ADB/Frida/BillingClient implementation, **not rewritten** |
| `setup_env.py` | Original Windows environment setup |
| `query_sku.py` | Original offer/product query helper |
| `一键安装环境.bat`, `0_环境自检.bat` | Original setup and preflight batch files |
| `1_查看offer列表.bat` | Original offer-listing batch file |
| `2_Pro_12个月_第1步.bat` … `5_Pro_备用6个月.bat` | Original checkout stages |
| `scripts/playwright-android.mjs` | Additive Playwright/ADB wrapper and optional Python command dispatcher |
| `PLAYWRIGHT.md` | Full Playwright-specific instructions |
| `README.zh-CN.md`, `使用说明.txt` | Original Chinese documentation |
| `.github/workflows/static-checks.yml` | Syntax and pure unit tests; no real Android billing |
| `SECURITY.md` | Operational/security limitations |

## 8. Security and limitations

- **Original code preserved:** The checkout flow can interact with the Google Play purchase screen automatically. `--force` is an account-check bypass in this script. Validate the account and all charges before running anything that could buy or renew a subscription.
- **No verified two-year entitlement:** Offer availability, stacking, renewal terms and approval are determined by Google. The original author's claims may not apply to your account or region.
- **Sensitive data:** Do not store or commit Google passwords, 2FA seeds, card details, payment tokens, `accounts.txt`, reports or screenshots. Prefer a test environment and authorized accounts.
- **No live validation in CI:** The repository CI does not use a Google account, rooted Android emulator or payment method.
- **Independent project:** Not affiliated with or endorsed by Google.

See [Playwright guide](PLAYWRIGHT.md), [security notes](SECURITY.md), and [the original Chinese instructions](使用说明.txt).
