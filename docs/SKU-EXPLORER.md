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
3. In the **Step 1** card, click **Check SKU & prices** next to **Check Device & Offers**. Check SKU is now an *option within Step 1*, not an additional numbered step or sidebar navigation item.
4. In the SKU details window select **AI Pro**, **Ultra** or **Custom**, then click **Check SKU (read-only)**. Custom expects a full Google Play product ID starting with `g1.`, e.g. `g1.2tb.ai.subs_variant`.
5. Review the observed base plans, offer IDs, ordered price phases and billing periods. A displayed 0 price is **not** evidence of eligibility or an active subscription.
6. Click **Close SKU Explorer** to return to Step 1. This lookup cannot start Step 2 or change account/device or checkout readiness. The original numbered Steps 0–5 remain unchanged.

If the modal’s **Check SKU** button is disabled, complete Step 1 again and confirm the active Google Play account. If it shows **Device/Google One/Frida is not ready**, verify that the same device and Google One process are running, and that the existing billing module and Frida server were prepared by Step 1. SKU Explorer intentionally does **not** auto-start, repair or install tooling.

**Safety and limits:** one manually chosen SKU per click; one bounded ProductDetails query; no billing flow, Subscribe tap, token export, account switching or automatic retry. Cancelling the check terminates the query process. No on-device or subscription result has been validated from this PR's CI; tests and screenshots use mocks/synthetic states.

## Dynamic Step 5+ discovery

**Step 1** now aggregates additional observed offers (not a separate step):

- The normal **Check Device & Offers** report supplies its offer IDs for the selected account/device.
- After a *real and verified* Step 1 execution, one bounded read-only query checks three existing known candidate product IDs (`g1.play.20tb`, `g1.play.ai.pro`, `g1.30tb`). The candidate list is not an exhaustive Google Play catalogue.
- **Check SKU & prices** can inspect a custom product manually; its sanitized returned offers are also added to the same Step 1 results.
- Steps **2, 3 and 4** remain the original Pro workflow, even if no extra offers are found.
- Additional distinct offers appear as **Step 5, Step 6, Step 7…**, with stable sorting, deduplication and a limit of 12 extra entries. If no additional offers are observed, Step 5+ is hidden.
- The pre-existing optional Pro +6-month operation is retained *only if* the corresponding known offer `6months-eft-ss-2026` on `g1.2tb.ai.subs_variant` is observed. In that case it is Step 5, and retains explicit payment approval and preflight checks.
- Unknown extra offers are **inspect-only**. Seeing a Step number does not authorize payment or mean the offer is redeemable; no generic checkout is inferred, and the guided sequence never automatically advances beyond Step 4.
- Discovered entries are session-bound. They are cleared when Step 1 is rerun or the selected account/device changes. No offers or product IDs are stored as new subscription status.

## Preview screenshots

Open [PR #85](https://github.com/hoangsvit/google-ai/pull/85) and find the automated **Terminal UI previews** comment. Images **09-sku-explorer.png**, **10-step1-check-sku.png** and **11-step1-discovered-offers.png** show the live SKU details window and the **Check SKU & prices** button beside the offer-check action inside Step 1, using synthetic data only. Both the main dashboard and SKU modal are captured without connecting a real Android device.

## Developer boundaries

- Dedicated query-only JS: `assets/frida/sku_query_readonly.js`.
- Runtime query bridge: `sku_check_runner.py`.
- Sanitization and price phase model: `sku_check_core.py`.
- Live Textual modal: `sku_explorer.py`.
- Offline tests: `tests/test_sku_check.py`.
- Original `query_sku.py` is **not** used; it previously printed offer tokens and loaded a JS module containing checkout functions.

If the selected device/account changes, rerun Step 1. Results are read-only metadata observations and must never unlock paid steps.
