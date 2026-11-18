# Google One / Google AI Pro — Android research scripts

**English documentation.** [中文原文](README.zh-CN.md) · [Original Chinese instructions](使用说明.txt) · [Playwright runner](PLAYWRIGHT.md)

This repository preserves the original third-party Python, ADB and Frida implementation from the supplied archive, including its original offer-query and checkout behavior. It is not affiliated with Google, and no eligibility or two-year subscription entitlement is guaranteed.

> **Important:** This is not a Playwright-only browser script. Play Billing is invoked in the Android Google One application through the original Python/Frida code. The original author implemented **automatic checkout interaction** in `ultra0.py`; opening or showing a zero-price offer does **not** prove that a purchase succeeded or that a 24-month term was awarded. Review all purchase and renewal terms. Avoid using primary accounts, credentials and payment-card data in plaintext files.

## Files

| File | Function |
|---|---|
| `ultra0.py` | **Original logic**: Android ADB + Frida, Google One BillingClient, offer query and billing flow |
| `setup_env.py` | Original Windows environment setup |
| `query_sku.py` | Original SKU query tool |
| `0_环境自检.bat` | Original Android environment check |
| `1_查看offer列表.bat` | Original offer listing |
| `2_Pro_12个月_第1步.bat` | Original first step |
| `3_Pro_加6个月_第2步.bat` | Original second step |
| `4_Pro_加6个月_第3步.bat` | Original third step |
| `5_Pro_备用6个月.bat` | Original optional step |
| `使用说明.txt` | Original author's Chinese instructions |
| `README.zh-CN.md` | Original Chinese README, preserved without changes |
| `scripts/playwright-android.mjs` | **Additive Playwright runner**, does not modify Python implementation |

## Requirements

- Windows and a properly authorized rooted Android phone or MuMu emulator, with ADB debugging enabled.
- Google Play Store and Google One installed on Android, with a Google account signed in.
- Python 3.10+, `adb`, and Frida compatible with the original script (`setup_env.py` installs 16.5.9).
- Node.js 22+ for Playwright integration. The experimental Playwright Android API needs ADB; browser checks additionally need Chrome on Android.

## Original script

The original `.bat` files remain available, unchanged. You can inspect available offers without launching checkout:

```powershell
python ultra0.py --account current@device --no-add --list --plan pro12
```

The original environment check can **install or start Frida and modify Android network settings**:

```powershell
python ultra0.py --check
```

## Playwright integration

```powershell
npm install
npm run android:doctor
npm run android:offers
```

`android:doctor` enumerates devices through Playwright's Android API and checks installed packages. `android:offers` starts the **original Python** query after the Playwright preflight; it does not open checkout. You can optionally verify Chrome on the emulator with `--browser-check` and save a private screenshot with `--screenshot <path>`.

The runner also exposes an explicitly acknowledged `run` command for invoking an original checkout step with the original account placeholder `current@device` (or optional `--email`). **It calls the unchanged Python script, which may interact automatically with Google Play checkout.** See [PLAYWRIGHT.md](PLAYWRIGHT.md) for the exact command and risks. The Playwright integration itself never fills card details, submits purchases or circumvents offer eligibility.

## Limitations and security

- Google Play Billing offer eligibility and the effect of subscription-replacement modes are controlled by Google, not by this repository. The author's 12+6+6 month claim remains unverified.
- Native Android / Play Billing remains dependent on MuMu/physical Android + ADB + Frida. Chromium running on a GitHub Actions hosted runner is not a replacement.
- Original code uses `--force` in `.bat` scripts and includes a payment UI auto-confirmation routine. **These behaviors are preserved at your request**, not endorsed as safe. The new runner uses the **same original `--force` flag** and `current@device` account placeholder by default; `--force` bypasses the original account-check guard, so verify the signed-in account independently.
- Original `ultra0.py` can read subscription data from Google Play databases, change proxy settings, and create reports. Review it before using it with any account.
- Never publish `accounts.txt`, access tokens, passwords, screenshots of personal data, or payment details. The `.gitignore` excludes the obvious generated files.
- No real Android device, Google account or billing action is exercised in the repository's CI.

See [PLAYWRIGHT.md](PLAYWRIGHT.md) and the original [Chinese README](README.zh-CN.md) for the two supported workflows.
