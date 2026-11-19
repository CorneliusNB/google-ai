"""Offline tests for explicit, fail-closed manual Android verification."""
import io
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
