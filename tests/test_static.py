"""No-device tests: do not start Frida, ADB, or Google Play checkout."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("google_ai_script", ROOT / "ultra0.py")
script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(script)


class StaticSafetyTests(unittest.TestCase):
    def test_python_compilation(self):
        for name in ("ultra0.py", "setup_env.py", "query_sku.py"):
            compile((ROOT / name).read_bytes(), name, "exec")

    def test_plan_substitutions(self):
        js = script.build_js("pro12", list_only=True)
        self.assertIn('var PRODUCTS=["g1.2tb.ai.subs_variant"]', js)
        self.assertIn('var PREFER="12months-eft"', js)
        self.assertIn('var LIST_ONLY=true', js)
        js2 = script.build_js("pro6", stack=True, old_token="token-test", stack_mode=5)
        self.assertIn('var STACK=true', js2)
        self.assertIn('var OLD_TOKEN="token-test"', js2)
        self.assertIn('var STACK_MODE=5', js2)

    def test_manual_timeout_is_not_success(self):
        with patch.object(script, "note") if hasattr(script, "note") else patch("builtins.print"):
            self.assertFalse(script.wait_human("unit-test", timeout=0))
        self.assertFalse(script.WAITING["on"])

    def test_checkout_observation_never_clicks(self):
        xml = '<node text="Subscribe JP¥0 Today JP¥2900 later" content-desc="" bounds="[1,1][200,90]" class="x" />'
        with patch.object(script, "ui_xml", return_value=xml), \
             patch.object(script, "tap_text") as clicked:
            result = script.confirm_zero(wait=2)
        self.assertEqual(result["price"], "JP¥0")
        self.assertFalse(result["confirmed"])
        self.assertTrue(result["manual_review_required"])
        clicked.assert_not_called()

    def test_ineligible_never_clicks(self):
        xml = '<node text="This account is not eligible" content-desc="" bounds="[1,1][200,90]" class="x" />'
        with patch.object(script, "ui_xml", return_value=xml), \
             patch.object(script, "tap_text") as clicked:
            result = script.confirm_zero(wait=2)
        self.assertTrue(result["ineligible"])
        clicked.assert_not_called()

    def test_wrong_account_aborts_before_launch(self):
        with patch.object(script, "current_play_account", return_value="other@example.com"), \
             patch.object(script, "launch_app") as launch, \
             patch.dict(script.__dict__, {"SKIP_ACCOUNT_CHECK": False}):
            result = script.process("owner@example.com", add=False, no_switch=True)
        self.assertEqual(result["status"], "wrong_account")
        launch.assert_not_called()

    def test_force_denied_for_checkout(self):
        with patch.object(sys, "argv", ["ultra0.py", "--force", "--account", "someone@example.com"]):
            with self.assertRaises(SystemExit) as raised:
                script.main()
        self.assertEqual(raised.exception.code, 2)

    def test_purchase_token_requires_account_and_active_subscription(self):
        now = int(time.time() * 1000)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "library.db"
            with sqlite3.connect(path) as con:
                con.execute("CREATE TABLE ownership (account TEXT, subs_valid_until_time INTEGER, inapp_purchase_data TEXT, doc_id TEXT)")
                for account, expiry, token in (
                    ("wrong@example.com", now + 5000000, "wrong-token"),
                    ("owner@example.com", now - 1000, "expired-token"),
                    ("owner@example.com", now + 2000000, "valid-token"),
                ):
                    con.execute("INSERT INTO ownership VALUES (?,?,?,?)", (account, expiry, json.dumps({"purchaseToken": token}), "g1.2tb.ai.subs_variant"))
                con.commit()
            raw = path.read_bytes()

        def fake_sh(*args, **kwargs):
            return "uid=0(root)" if args == ("shell", "id") else raw

        with patch.object(script, "sh", side_effect=fake_sh):
            self.assertEqual(script.read_purchase_token("subs_variant", "owner@example.com"), "valid-token")
            self.assertEqual(script.read_purchase_token("subs_variant", "missing@example.com"), "")
            self.assertEqual(script.read_purchase_token("subs_variant", "not-an-email"), "")

    def test_missing_subscription_never_opens_checkout(self):
        with patch.object(script, "current_play_account", return_value="owner@example.com"), \
             patch.object(script, "read_purchase_token", return_value=""), \
             patch.object(script, "launch_app") as launched, \
             patch.dict(script.__dict__, {"SKIP_ACCOUNT_CHECK": False}):
            result = script.process("owner@example.com", add=False, no_switch=True, stack=True)
        self.assertEqual(result["status"], "matching_active_subscription_not_found")
        launched.assert_not_called()

    def test_frida_detaches_and_redacts_offer_token(self):
        class Session:
            def __init__(self):
                self.detached = False
                self.cb = None
            def create_script(self, js):
                self.js = js
                return self
            def on(self, typ, cb):
                self.cb = cb
            def load(self):
                self.cb({"payload": {"ev": "offer", "id": "trial", "token": "secret", "micros": "0"}}, None)
                self.cb({"payload": {"ev": "list_only"}}, None)
            def detach(self):
                self.detached = True

        session = Session()
        frida = types.SimpleNamespace(get_usb_device=lambda timeout: types.SimpleNamespace(attach=lambda pid: session))
        with patch.dict(sys.modules, {"frida": frida}):
            result = script.run_trial(123, wait=0.5, list_only=True)
        self.assertTrue(session.detached)
        self.assertEqual(result["offers"], [{"ev": "offer", "id": "trial", "micros": "0"}])
        self.assertFalse(result["errors"])

    def test_frida_script_syntax(self):
        try:
            check = subprocess.run(["node", "--check"], input=script.FRIDA_JS, capture_output=True, text=True, timeout=10)
        except FileNotFoundError:
            self.skipTest("node not installed")
        self.assertEqual(check.returncode, 0, check.stderr)

    def test_batch_files_dont_bypass_checkout_account_check(self):
        for bat in ROOT.glob("*.bat"):
            if bat.name.startswith(("2_", "3_", "4_", "5_")):
                self.assertNotIn("--force", bat.read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
