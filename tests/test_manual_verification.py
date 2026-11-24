"""Offline tests for explicit, fail-closed manual Android verification."""
import io
from subprocess import CompletedProcess
import threading
import unittest
from unittest.mock import patch

import ultra0


class BlockingInput:
    def __init__(self):
        self.release = threading.Event()

    def readline(self):
        self.release.wait(1)
        return "\n"


class ManualVerificationTests(unittest.TestCase):
    def test_ui_dump_failure_cannot_return_an_old_hierarchy(self):
        stale = b'<hierarchy><node text="stale"/></hierarchy>'
        fresh = b'<hierarchy><node text="fresh"/></hierarchy>'
        results = [
            CompletedProcess([], 1, stdout=stale, stderr=b"dump failed"),
            CompletedProcess([], 0, stdout=fresh, stderr=b""),
        ]
        with patch.object(ultra0.subprocess, "run", side_effect=results) as run:
            self.assertEqual(ultra0.ui_xml(), "")
            self.assertEqual(ultra0.ui_xml(), fresh.decode())

        first, second = (call.args[0][-1] for call in run.call_args_list)
        for command in (first, second):
            self.assertRegex(
                command,
                r"^trap 'rm -f (/sdcard/eplus-ui-[0-9a-f]{32}\.xml)' EXIT; "
                r"uiautomator dump \1 >/dev/null && cat \1$",
            )
        self.assertNotEqual(first, second)

    def test_incomplete_ui_dump_is_ignored(self):
        with patch.object(ultra0, "sh", return_value="<hierarchy><node/>"):
            self.assertEqual(ultra0.ui_xml(), "")

    def test_enter_acknowledgement_allows_continue(self):
        with patch.object(ultra0.sys, "stdin", io.StringIO("\n")):
            self.assertTrue(ultra0.wait_human("Test-only prompt", timeout=1))
        self.assertFalse(ultra0.WAITING["on"])

    def test_closed_stdin_never_counts_as_approval(self):
        with patch.object(ultra0.sys, "stdin", io.StringIO("")):
            self.assertFalse(ultra0.wait_human("Test-only prompt", timeout=1))
        self.assertFalse(ultra0.WAITING["on"])

    def test_timeout_does_not_fall_through_as_success(self):
        blocked = BlockingInput()
        try:
            with patch.object(ultra0.sys, "stdin", blocked):
                self.assertFalse(ultra0.wait_human("Test-only prompt", timeout=0.05))
            self.assertFalse(ultra0.WAITING["on"])
        finally:
            blocked.release.set()

    def test_card_setup_does_not_invent_billing_address(self):
        fields = [{"cls": "EditText", "x": 10, "y": 20}] * 7
        card = {"number": "4111111111111111", "exp": "0129",
                "cvc": "000", "holder": "Actual Name"}
        with patch.object(ultra0, "sh"), \
             patch.object(ultra0, "tap_text", return_value=True), \
             patch.object(ultra0, "nodes", return_value=fields), \
             patch.object(ultra0, "ui_xml", return_value="<xml/>"), \
             patch.object(ultra0, "tap"), \
             patch.object(ultra0, "type_text") as text_input, \
             patch.object(ultra0, "wait_human", return_value=True) as confirm, \
             patch.object(ultra0.time, "sleep"):
            self.assertTrue(ultra0.add_card(card))
        entered = [call.args[0] for call in text_input.call_args_list]
        self.assertEqual(entered, ["4111111111111111", "01", "29", "000", "Actual Name"])
        self.assertNotIn("123 Main St", entered)
        self.assertNotIn("Portland", entered)
        confirm.assert_called_once()

    def test_unconfirmed_payment_method_prevents_checkout(self):
        with patch.object(ultra0, "add_card", return_value=False) as add, \
             patch.object(ultra0, "launch_app") as launch:
            report = ultra0.process(
                "test@example.com", add=False,
                card={"number": "test", "exp": "0129", "cvc": "000", "holder": "Test"})
        self.assertEqual(report["status"], "payment_method_not_confirmed")
        add.assert_called_once()
        launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
