"""Ensure upstream-style multi-ID discovery is confined to the non-purchasing path."""
import importlib.util
from pathlib import Path
import unittest

source = Path(__file__).resolve().parents[1] / "ultra0.py"
spec = importlib.util.spec_from_file_location("readonly_product_probe", source)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class ReadonlyProductProbeTests(unittest.TestCase):
    def test_list_only_queries_both_pro_trial_products_plus_regular_product(self):
        js = app.build_js(plan="pro12", list_only=True)
        self.assertIn(
            'var PRODUCTS=["g1.2tb.ai.subs_variant","g1.play.2tb.ai","g1.2tb.ai"];',
            js,
        )
        self.assertIn("var LIST_ONLY=true;", js)

    def test_paid_stage_keeps_single_existing_target(self):
        for plan in ("pro12", "pro6", "pro6b", "pro6c"):
            js = app.build_js(plan=plan, list_only=False)
            self.assertIn('var PRODUCTS=["g1.2tb.ai.subs_variant"];', js)
            self.assertNotIn('var PRODUCTS=["g1.2tb.ai.subs_variant","g1.play.2tb.ai"', js)
            self.assertNotIn("var LIST_ONLY=true;", js)

    def test_listing_does_not_enable_stack(self):
        js = app.build_js(plan="pro12", list_only=True)
        self.assertNotIn("var STACK=true;", js)
        self.assertNotIn("var OLD_TOKEN=", js)


if __name__ == "__main__":
    unittest.main()
