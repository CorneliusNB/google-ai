"""SKU Explorer safety and offline regression tests; no Android/emulator needed."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

import sku_check_core as core
import sku_check_runner as runner

ROOT = Path(__file__).resolve().parents[1]


class SKUMetadataTests(unittest.TestCase):
    def test_requires_explicit_bounded_skus(self):
        self.assertEqual(
            core.validate_skus(["g1.2tb.ai.subs_variant", "g1.2tb.ai.subs_variant"]),
            ["g1.2tb.ai.subs_variant"])
        for invalid in ([], ["not-sku"], ["g1.x;rm -rf"], ["g1.2tb"] * 11):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                core.validate_skus(invalid)

    def test_ordered_phases_and_token_stripping(self):
        payload = [{
            "sku": "g1.2tb.ai.subs_variant",
            "offer_id": "test-offer",
            "base_plan_id": "yearly",
            "token": "SECRET-DO-NOT-STORE",
            "email": "secret@example.com",
            "phases": [
                {
                    "price_amount_micros": "0",
                    "currency": "USD", "billing_period": "P1M",
                    "billing_cycle_count": 1, "recurrence_mode": 2,
                    "purchaseToken": "VERY-SECRET",
                },
                {
                    "price_amount_micros": "19990000",
                    "currency": "USD", "billing_period": "P1M",
                    "billing_cycle_count": 0, "recurrence_mode": 1,
                },
            ],
        }]
        got = core.sanitize_offers(payload, ["g1.2tb.ai.subs_variant"])
        self.assertEqual(got["status"], "observed")
        self.assertEqual(len(got["items"][0]["phases"]), 2)
        self.assertFalse(got["eligibility_verified"])
        self.assertFalse(got["subscription_active_verified"])
        self.assertNotIn("SECRET", str(got))
        self.assertNotIn("secret@example.com", str(got))
        text = core.render_result(got)
        self.assertIn("0.00 USD / P1M", text)
        self.assertIn("19.99 USD / P1M", text)
        self.assertIn("UNVERIFIED", text)
        self.assertNotIn("token", text.lower())

    def test_rejects_missing_currency_and_malformed_phases(self):
        result = core.sanitize_offers([{
            "sku": "g1.play.20tb", "offer_id": "example",
            "base_plan_id": "monthly", "phases": [{
                "price_amount_micros": "19990000",
                "billing_period": "P1M", "currency": "UNKNOWN"
            }]
        }], ["g1.play.20tb"])
        self.assertEqual(result["status"], "not_returned")
        self.assertEqual(result["items"], [])

    def test_missing_and_no_offers_are_distinct(self):
        self.assertEqual(
            core.sanitize_offers([], ["g1.play.20tb"])["status"], "not_returned")
        self.assertEqual(
            core.sanitize_offers([{"sku": "g1.play.20tb", "no_offers": True}],
                                 ["g1.play.20tb"])["status"],
            "no_offers")

    def test_runner_fails_closed_without_adb(self):
        with patch.object(runner, "find_adb", return_value=None):
            out = runner.check_skus("emulator-5554", ["g1.play.20tb"])
        self.assertEqual(out["status"], "device_not_ready")
        self.assertEqual(out["items"], [])

    def test_runner_fails_closed_for_invalid_serial(self):
        with patch.object(runner, "find_adb", side_effect=RuntimeError("must not be called")) as find:
            out = runner.check_skus("../../bad", ["g1.play.20tb"])
            find.assert_not_called()
        self.assertEqual(out["status"], "device_not_ready")

    def test_query_javascript_has_no_checkout_path(self):
        js = (ROOT / "assets/frida/sku_query_readonly.js").read_text(encoding="utf-8")
        for forbidden in (
            "launchBillingFlow", "BillingFlowParams", "setOfferToken",
            "getOfferToken", "getPurchaseToken", "queryPurchasesAsync",
            "setOldPurchaseToken", "input tap"
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, js)
        self.assertIn("queryProductDetailsAsync", js)

    def test_ui_never_runs_existing_checkout_script(self):
        source = (ROOT / "sku_explorer.py").read_text(encoding="utf-8")
        self.assertIn("sku_check_runner.py", source)
        self.assertNotIn("query_sku.py", source)
        self.assertNotIn("ultra0.py", source)
        self.assertNotIn("run-all.ps1", source)


@unittest.skipUnless(importlib.util.find_spec("textual") is not None,
                     "Textual is tested in Terminal UI previews with dependencies installed")
class SKUExplorerUITests(unittest.IsolatedAsyncioTestCase):
    async def test_step_one_sku_button_opens_without_adding_a_new_step(self):
        from tempfile import TemporaryDirectory

        from textual.widgets import Button, Select, Static
        from sku_explorer import SKUExplorer
        from tui import GoogleAITUI

        with TemporaryDirectory() as directory:
            app = GoogleAITUI(repo=Path(directory))
            async with app.run_test(size=(110, 35)) as pilot:
                self.assertEqual(len(app.query("#workflow .workflow-step")), 6)
                self.assertIn("1. Available offers", str(app.query_one("#stage_1", Static).render()))
                button = app.query_one("#sku_explorer", Button)
                self.assertTrue(button.visible)
                self.assertGreater(button.region.width, 10)
                self.assertTrue(app.query_one("#quickstart", Button).visible)
                self.assertEqual(app.query_one("#step", Select).value, 1)
                with patch.object(app, "_start") as paid:
                    await pilot.click("#sku_explorer")
                    await pilot.pause()
                    paid.assert_not_called()
                self.assertIsInstance(app.screen, SKUExplorer)
                self.assertTrue(app.screen.query_one("#sku_check", Button).disabled)
                with patch.object(app, "selected_pressed") as start:
                    app.action_run_selected()
                    start.assert_not_called()
                await pilot.click("#sku_close")
                await pilot.pause()
                self.assertFalse(app._offer_check_ready)
                self.assertEqual(app.query_one("#step", Select).value, 1)

    async def test_extra_offers_become_steps_5_and_6_without_checkout(self):
        from tempfile import TemporaryDirectory
        from textual.widgets import Button, Select, Static
        from offer_discovery import parse_step1
        from sku_explorer import SKUExplorer
        from tui import GoogleAITUI

        with TemporaryDirectory() as directory:
            app = GoogleAITUI(repo=Path(directory))
            async with app.run_test(size=(110, 35)) as pilot:
                self.assertFalse(app.query_one("#stage_5", Static).display)
                self.assertEqual(app.query_one("#step", Select).value, 1)
                app._checked_device = "emulator-5554"
                app._offer_ready_device = "emulator-5554"
                app._offer_ready_account = "verified@example.test"
                app._offer_check_ready = True
                app._update_discovered(parse_step1({"offers": [
                    {"product": "g1.2tb.ai.subs_variant", "id": "12months-eft"},
                    {"product": "g1.play.20tb", "id": "offer-a"},
                    {"product": "g1.30tb", "id": "offer-b"},
                ]}))
                await pilot.pause()
                self.assertEqual(len(app._extra_offers), 2)
                self.assertTrue(app.query_one("#stage_5", Static).display)
                self.assertIn("5. Ultra:", str(app.query_one("#stage_5", Static).render()))
                self.assertIn("6. Ultra:", str(app.query_one("#stage_6", Static).render()))
                app.query_one("#step", Select).value = 5
                await pilot.pause()
                self.assertEqual(app._selected(), 5)
                self.assertEqual(str(app.query_one("#run", Button).label),
                                 "Inspect observed offer")
                with patch.object(app, "_start") as paid:
                    app.selected_pressed()
                    await pilot.pause()
                    paid.assert_not_called()
                self.assertIsInstance(app.screen, SKUExplorer)
                await pilot.click("#sku_close")
                await pilot.pause()
                self.assertFalse(app.busy)

                # A fresh check without additional offers removes those steps.
                app._update_discovered([], replace=True)
                await pilot.pause()
                self.assertFalse(app.query_one("#stage_5", Static).display)
                self.assertFalse(app.query_one("#stage_6", Static).display)
                self.assertEqual(app.query_one("#step", Select).value, 1)

    async def test_sku_dialog_does_not_unlock_paid_steps(self):
        from tempfile import TemporaryDirectory
        from textual.widgets import Button
        from tui import GoogleAITUI

        with TemporaryDirectory() as directory:
            app = GoogleAITUI(repo=Path(directory))
            async with app.run_test(size=(110, 35)) as pilot:
                app._start(6, False)  # No synthetic Step 1A should ever be executable.
                await pilot.pause()
                self.assertFalse(app.busy)
                self.assertIsNone(app.current_step)
                self.assertFalse(app._offer_check_ready)
                app.busy = True
                await pilot.click("#sku_explorer")
                await pilot.pause()
                self.assertEqual(len(app.screen.query("#sku_check")), 0)


if __name__ == "__main__":
    unittest.main()
