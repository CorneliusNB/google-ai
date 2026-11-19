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
    async def test_application_branding(self):
        from tui import GoogleAITUI
        self.assertEqual(GoogleAITUI.TITLE, "ePlus AI Toolkit")
        self.assertEqual(GoogleAITUI.SUB_TITLE, "ePlus.DEV")

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

    async def test_first_run_shows_clear_workflow_mode(self):
        from textual.widgets import Button, Select, Static
        from tui import GoogleAITUI
        with tempfile.TemporaryDirectory() as directory:
            app = GoogleAITUI(repo=Path(directory))
            with patch("tui.subprocess.Popen") as popen:
                async with app.run_test(size=(90, 20)) as pilot:
                    self.assertEqual(app.query_one("#mode", Select).value, "single")
                    self.assertEqual(app.query_one("#step", Select).value, 1)
                    self.assertFalse(app.query_one("#stop", Button).display)
                    self.assertFalse(app.query_one("#next", Button).display)
                    self.assertIn("Run selected step", str(app.query_one("#run", Button).label))
                    app.query_one("#mode", Select).value = "all"
                    await pilot.pause()
                    self.assertTrue(app.query_one("#step", Select).disabled)
                    self.assertIn("Run all", str(app.query_one("#run", Button).label))
                popen.assert_not_called()

    async def test_all_and_from_modes_route_to_expected_step(self):
        from textual.widgets import Select
        from tui import GoogleAITUI
        with tempfile.TemporaryDirectory() as directory:
            app = GoogleAITUI(repo=Path(directory))
            with patch.object(GoogleAITUI, "_confirm_stage") as confirm:
                async with app.run_test(size=(110, 35)) as pilot:
                    app.query_one("#mode", Select).value = "all"
                    await pilot.pause()
                    app.selected_pressed()
                    confirm.assert_called_with(2, True)
                    app.query_one("#mode", Select).value = "from"
                    app.query_one("#step", Select).value = 4
                    await pilot.pause()
                    app.selected_pressed()
                    confirm.assert_called_with(4, True)
                    app.query_one("#mode", Select).value = "single"
                    await pilot.pause()
                    app.selected_pressed()
                    confirm.assert_called_with(4, False)

    async def test_busy_state_locks_run_controls_but_keeps_help_available(self):
        from textual.widgets import Button, Select
        from tui import GoogleAITUI
        with tempfile.TemporaryDirectory() as directory:
            app = GoogleAITUI(repo=Path(directory))
            with patch.object(GoogleAITUI, "run_stage"):
                async with app.run_test(size=(110, 35)) as pilot:
                    app._start(1, False)
                    self.assertTrue(app.query_one("#run", Button).disabled)
                    self.assertTrue(app.query_one("#mode", Select).disabled)
                    self.assertTrue(app.query_one("#step", Select).disabled)
                    self.assertTrue(app.query_one("#quickstart", Button).disabled)
                    self.assertFalse(app.query_one("#nav_help", Button).disabled)
                    self.assertFalse(app.query_one("#debug", Button).disabled)
                    self.assertTrue(app.query_one("#stop", Button).display)

    async def test_stop_is_real_only_for_read_only_checks(self):
        from tui import GoogleAITUI
        from textual.widgets import Button
        with tempfile.TemporaryDirectory() as directory:
            app = GoogleAITUI(repo=Path(directory))
            with patch.object(GoogleAITUI, "terminate_readonly_child") as stop:
                async with app.run_test(size=(110, 35)):
                    app.busy = True
                    app.current_step = 1
                    app.stop_pressed()
                    self.assertTrue(app._cancel_requested)
                    stop.assert_called_once()
                    app._cancel_requested = False
                    app.current_step = 3
                    app.stop_pressed()
                    self.assertTrue(app._stop_after_step)
                    self.assertFalse(app._cancel_requested)
                    self.assertTrue(app.query_one("#stop", Button).disabled)

    async def test_quit_during_checkout_queues_exit_without_killing_process(self):
        from tui import GoogleAITUI
        from textual.widgets import Button
        with tempfile.TemporaryDirectory() as directory:
            app = GoogleAITUI(repo=Path(directory))
            with patch.object(GoogleAITUI, "terminate_readonly_child") as stop:
                async with app.run_test(size=(110, 35)):
                    app.busy = True
                    app.current_step = 3
                    app.action_quit_safely()
                    self.assertTrue(app._exit_after_step)
                    self.assertTrue(app._stop_after_step)
                    self.assertFalse(app._cancel_requested)
                    self.assertTrue(app.query_one("#exit", Button).disabled)
                    stop.assert_not_called()

    async def test_quit_during_readonly_requests_stop(self):
        from tui import GoogleAITUI
        with tempfile.TemporaryDirectory() as directory:
            app = GoogleAITUI(repo=Path(directory))
            with patch.object(GoogleAITUI, "terminate_readonly_child") as stop:
                async with app.run_test(size=(110, 35)):
                    app.busy = True
                    app.current_step = 0
                    app.action_quit_safely()
                    self.assertTrue(app._exit_after_step)
                    self.assertTrue(app._cancel_requested)
                    stop.assert_called_once()

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
