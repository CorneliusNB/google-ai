"""Offline tests for the Textual frontend and its safe execution boundary."""
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from tui_core import (
    command_for_step, mask_email, needs_setup, outcome_for_stage,
    read_fresh_report, validate_step,
)


class CoreTests(unittest.TestCase):
    def test_setup_only_when_pinned_frida_is_missing(self):
        with patch("tui_core.importlib.metadata.version", return_value="16.5.9"):
            self.assertFalse(needs_setup())
        with patch("tui_core.importlib.metadata.version", return_value="16.4.0"):
            self.assertTrue(needs_setup())
        from importlib.metadata import PackageNotFoundError
        with patch("tui_core.importlib.metadata.version", side_effect=PackageNotFoundError):
            self.assertTrue(needs_setup())

    def test_step_range(self):
        for step in range(6):
            self.assertEqual(validate_step(step), step)
        for value in (-1, 6, "2", True):
            with self.assertRaises(ValueError):
                validate_step(value)

    def test_reuses_single_step_powershell_wrapper(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            (p / "run-all.ps1").write_text("# test")
            command = command_for_step(3, p, shell="powershell.exe")
            self.assertEqual(command[-4:], ["-File", str(p / "run-all.ps1"), "-Step", "3"])
            self.assertNotIn("-AllStages", command)
            self.assertNotIn("-Force", command)

    def test_no_shell_or_script_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(FileNotFoundError):
                command_for_step(1, Path(folder), shell="pwsh")

    def test_stale_reports_cannot_confirm_old_checkout(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "report"
            p.mkdir()
            f = p / "test.json"
            f.write_text(json.dumps({"status": "checkout_requested"}))
            now = time.time()
            import os
            os.utime(f, (now - 600, now - 600))
            self.assertIsNone(read_fresh_report(p, 3, now))
            result = outcome_for_stage(3, 0, None)
            self.assertFalse(result.can_review)

    def test_security_block_and_duplicate_cannot_continue(self):
        for reason in ("payment_security_blocked", "already_subscribed",
                       "trial_duration_unverified"):
            result = outcome_for_stage(3, 0, {
                "status": "checkout_not_confirmed", "sheet": {"reason": reason}
            })
            self.assertFalse(result.can_review)

    def test_requested_is_not_claimed_active(self):
        result = outcome_for_stage(3, 0, {"status": "checkout_requested"})
        self.assertTrue(result.can_review)
        self.assertNotIn("activated", result.title.lower())
        self.assertIn("Check Google Play", result.instruction)

    def test_exit_error_never_allows_next(self):
        result = outcome_for_stage(3, 1, {"status": "checkout_requested"})
        self.assertFalse(result.can_review)

    def test_account_mask(self):
        self.assertEqual(mask_email("example@gmail.com"), "ex***@gmail.com")
        self.assertEqual(mask_email("invalid"), "Not detected")


class TextualSmokeTests(unittest.IsolatedAsyncioTestCase):
    async def test_tui_loads_without_starting_any_checkout(self):
        from textual.widgets import Button, Select, Static
        from tui import GoogleAITUI

        with tempfile.TemporaryDirectory() as directory:
            app = GoogleAITUI(repo=Path(directory), selected_step=3)
            with patch("tui.subprocess.Popen") as popen:
                async with app.run_test(size=(110, 35)) as pilot:
                    self.assertEqual(app.query_one("#step", Select).value, 3)
                    self.assertIn("Ready", str(app.query_one("#state", Static).render()))
                    self.assertTrue(app.query_one("#next", Button).disabled)
                    await pilot.press("d")
                    self.assertTrue(app.debug_visible)
                popen.assert_not_called()

    async def test_first_run_shows_simple_action_and_hides_advanced(self):
        from textual.containers import Vertical
        from textual.widgets import Button, Static
        from tui import GoogleAITUI

        with tempfile.TemporaryDirectory() as directory:
            app = GoogleAITUI(repo=Path(directory))
            with patch("tui.subprocess.Popen") as popen:
                async with app.run_test(size=(90, 20)) as pilot:
                    self.assertFalse(app.query_one("#advanced", Vertical).display)
                    self.assertFalse(app.query_one("#stop", Button).display)
                    self.assertFalse(app.query_one("#next", Button).display)
                    self.assertIn("Ready", str(app.query_one("#state", Static).render()))
                    await pilot.click("#advanced_toggle")
                    await pilot.pause()
                    self.assertTrue(app.query_one("#advanced", Vertical).display)
                popen.assert_not_called()

    async def test_step_click_requires_approval_before_subprocess(self):
        from tui import GoogleAITUI, Approval

        with tempfile.TemporaryDirectory() as directory:
            app = GoogleAITUI(repo=Path(directory), selected_step=3)
            with patch("tui.subprocess.Popen") as popen:
                async with app.run_test(size=(110, 35)) as pilot:
                    await pilot.click("#run")
                    await pilot.pause()
                    self.assertIsInstance(app.screen, Approval)
                    await pilot.click("#cancel")
                    await pilot.pause()
                    popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
