# Using SKU Explorer (read-only)

This feature is available on the research branch `research/one-sku-billing-study` and its PR until merged. It is **not yet available on the default `main` release**. Google Play product metadata is not a subscription or eligibility guarantee.

## Start the app

Use your existing installation, but check out the research branch first (first-time clone only):

```sh
git fetch origin
git switch --track origin/research/one-sku-billing-study
git pull --ff-only
```

- Windows: launch `./run-all.ps1` in PowerShell (use `.\run-all.ps1` on Windows).
- macOS: `sh run-macos.sh`.
- Linux (on branches with the Linux launcher): `sh run-linux.sh`.

If you already have the branch locally, run `git switch research/one-sku-billing-study` followed by `git pull --ff-only` instead.

### Check SKU from the Textual dashboard

1. Start your Android device/emulator and confirm Google Play Store and Google One are installed, signed in to the account you intend to check, with ADB and Frida available.
2. Click **Check Device & Offers** (Step 1) first. This establishes the device and Play-account status. Step 1 can perform environment preparation; read [SECURITY.md](../SECURITY.md) before running.
3. In the **STEPS** list, look for **1A. Check SKU (read-only)**, between **1. Available offers** and **2. Pro 12 months**. The original numbered Steps 0–5 are unchanged.
4. Click **Choose another step +**, select **1A. Check SKU (read-only)** from the same dropdown used for normal steps, then click **Run Check SKU (read-only)**. It uses single-step mode only; no checkout sequence starts.
5. In the SKU step panel, choose **AI Pro**, **Ultra** or **Custom** to fill the product ID, then click **Check SKU (read-only)**. Custom requires a full ID beginning with `g1.`, e.g. `g1.2tb.ai.subs_variant`.
6. Review returned offer/base plan and ordered price phases. A zero-priced phase does **not** confirm eligibility. Click **Close SKU Explorer** to return to the dashboard. The 1A indicator reflects only query completion, not subscription activation.

If **Check SKU** is disabled, do Step 1 again and confirm the active Google Play account. If it shows **Device/Google One/Frida is not ready**, verify that the same device and Google One process are running, and that the existing billing module and Frida server were prepared by Step 1. SKU Explorer intentionally does **not** auto-start, repair or install tooling.

**Safety and limits:** one manually chosen SKU per click; one bounded ProductDetails query; no billing flow, Subscribe tap, token export, account switching or automatic retry. Cancelling the check terminates the query process. No on-device or subscription result has been validated from this PR's CI; tests and screenshots use mocks/synthetic states.

## Preview screenshots

Open [PR #85](https://github.com/hoangsvit/google-ai/pull/85) and find the automated **Terminal UI previews** comment. Images **09-sku-explorer.png** and **10-sku-step-selection.png** show the real step dialog and the native dropdown route from the dashboard, using synthetic data only. Both the main dashboard and SKU modal are captured without connecting a real Android device.

## Developer boundaries

- Dedicated query-only JS: `assets/frida/sku_query_readonly.js`.
- Runtime query bridge: `sku_check_runner.py`.
- Sanitization and price phase model: `sku_check_core.py`.
- Live Textual modal: `sku_explorer.py`.
- Offline tests: `tests/test_sku_check.py`.
- Original `query_sku.py` is **not** used; it previously printed offer tokens and loaded a JS module containing checkout functions.

If the selected device/account changes, rerun Step 1. Results are read-only metadata observations and must never unlock paid steps.
