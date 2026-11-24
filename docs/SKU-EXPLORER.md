# Step 1 — Unified SKU and Offer Discovery

Step 1 includes **SKU inspection automatically**. There is only one action: **Check Device & Offers**. Do not click a separate SKU button or open a SKU Explorer window.

## Usage

1. Start ePlus AI Toolkit, select the intended Android device and Google Play account.
2. Click **Check Device & Offers** (Step 1). The existing checks verify the device/account and fetch the normal Pro offer listing.
3. After a successful **real, verified** Step 1, the toolkit also queries the following known ProductDetails SKUs **automatically**, using the same verified device:
   - `g1.2tb.ai.subs_variant`
   - `g1.play.20tb`
   - `g1.play.ai.pro`
   - `g1.30tb`
4. **SUPPORTED OFFERS · FIRST PHASE ONLY** shows observed offers that match an existing checkout step and have a zero-priced first phase.
5. The existing Steps **2, 3 and 4** remain in the step picker. The optional **Step 5** appears only when the scan returns its exact offer with a zero-priced first phase.

## Supported operations and safety

The original Pro optional +6-month operation is only available as Step 5 when its exact product/offer is observed in Step 1; it retains its original explicit approval and checkout preflight. Unknown discovered offers are **inspect-only** and never initiate a generic purchase. The guided checkout sequence does not automatically continue beyond Step 4.

Step 1's SKU check invokes `sku_check_runner.py` using a separate read-only Frida `queryProductDetailsAsync` script. It does **not** call `launchBillingFlow`, read a purchase token, switch accounts or automatically activate any plan. Finding a SKU, seeing a zero-priced phase, or seeing an offer ID **does not prove account eligibility, an active subscription, a free month or successful payment**. Verify terms and charges in Google Play before any optional checkout.

The candidate SKUs are a **bounded, known shortlist**, not an exhaustive Google Play catalogue, and returned offers may vary by region, time and account. GitHub Actions cannot confirm the device integration without a real authorized emulator.

New scans clear stale extra steps and SKU results. When the selected account/device changes, the old offer catalog is cleared so it cannot be mistaken for the current account.

## Historical CI screenshots and tests

See [PR #85](https://github.com/hoangsvit/google-ai/pull/85), the **Terminal UI previews** comment. GitHub Actions captures the actual running Textual dashboard with synthetic data and posts the images directly:

- `09-step1-sku-offers.png`: one Step 1 button and the supported offer list.
- `10-step1-sku-missing.png`: no supported offers found in a synthetic scan.
- `11-step1-discovered-offers.png`: the supported optional Step 5 is visible in a synthetic scan; unsupported offers are not shown as extra steps.

Automated tests: `tests/test_sku_check.py`, `tests/test_offer_discovery.py`, plus the existing TUI, Linux, macOS and Windows regression suites.

## Source files

- `tui.py`: Step 1 workflow, automatic SKU candidate scan and supported offer display.
- `sku_check_runner.py`: bounded device-bound ProductDetails query.
- `sku_check_core.py`: validation, sanitized offer data and safe pricing display.
- `offer_discovery.py`: deduplication and dynamic Step 5+ numbering.
- `assets/frida/sku_query_readonly.js`: query-only Android Billing instrumentation.
