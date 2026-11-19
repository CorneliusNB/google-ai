"""Mock-only macOS preview coverage. Never touch ADB, accounts or checkout."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import macos_runner
from tui_core import command_for_step

ROOT = Path(__file__).resolve().parents[1]


class MacDiagnosticTests(unittest.TestCase):
    def test_bridge_accepts_only_steps_zero_and_one(self):
        for step, flag in ((0, "--check"), (1, "--list")):
            with self.subTest(step=step):
                cmd = macos_runner.readonly_command(step, "emulator-5554", "python3")
                self.assertIn(flag, cmd)
                self.assertEqual(cmd[-2:], ["--serial", "emulator-5554"])
                for forbidden in ("--force", "--stack", "--old-token"):
                    self.assertNotIn(forbidden, cmd)
        listing = macos_runner.readonly_command(1, "emulator-5554")
        self.assertIn("--no-add", listing)
        self.assertIn("--no-switch", listing)
        self.assertIn("current@device", listing)
        for step in (-1, 2, 3, 4, 5, True):
            with self.assertRaises(ValueError):
                macos_runner.readonly_command(step, "emulator-5554")

    def test_preflight_does_not_guess_ambiguous_device(self):
        with patch("macos_runner.shutil.which", return_value="/opt/homebrew/bin/adb"):
            with patch("macos_runner.metadata.version", return_value="16.5.9"):
                with patch("macos_runner.online_serials", return_value=["one", "two"]):
                    with patch("macos_runner.auto_select_device", return_value=None):
                        with self.assertRaisesRegex(RuntimeError, "Multiple"):
                            macos_runner.preflight()
                    with patch("macos_runner.auto_select_device", return_value="one"):
                        self.assertEqual(macos_runner.preflight(), ("/opt/homebrew/bin/adb", "one"))
            with patch("macos_runner.metadata.version", return_value="17.0.0"):
                with self.assertRaisesRegex(RuntimeError, "16.5.9"):
                    macos_runner.preflight()

    def test_no_checkout_even_with_malformed_flags(self):
        with patch("macos_runner.preflight", return_value=("/usr/bin/adb", "one")):
            with patch("macos_runner.subprocess.call", return_value=0) as call:
                self.assertEqual(macos_runner.main(["--step", "1"]), 0)
                cmd = call.call_args.args[0]
                self.assertIn("--list", cmd)
                self.assertNotIn("--stack", cmd)
                self.assertEqual(call.call_args.kwargs["env"]["ADB_PATH"], "/usr/bin/adb")
            with patch("macos_runner.subprocess.call") as call:
                with self.assertRaises(SystemExit):
                    macos_runner.main(["--step", "2"])
                call.assert_not_called()

    def test_macos_step_routing_isolated_from_windows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "macos_runner.py").write_text("# mock", encoding="utf-8")
            with patch("tui_core.sys.platform", "darwin"):
                for step in (0, 1):
                    cmd = command_for_step(step, root)
                    self.assertEqual(cmd[0], sys.executable)
                    self.assertEqual(cmd[-2:], ["--step", str(step)])
                for step in (2, 3, 4, 5):
                    with self.assertRaises(ValueError):
                        command_for_step(step, root)


class MacTextualTests(unittest.IsolatedAsyncioTestCase):
    async def test_macos_ui_disables_all_paid_paths(self):
        from textual.widgets import Button, Select
        from tui import GoogleAITUI
        with tempfile.TemporaryDirectory() as temp:
            with patch("tui.is_macos_platform", return_value=True):
                app = GoogleAITUI(repo=Path(temp))
            with patch("tui.subprocess.Popen") as spawn:
                async with app.run_test(size=(100, 28)) as pilot:
                    self.assertEqual(app.query_one("#step", Select).value, 1)
                    self.assertTrue(app.query_one("#mode", Select).disabled)
                    self.assertFalse(app.query_one("#mode_field").display)
                    self.assertFalse(app.query_one("#sequence", Button).display)
                    self.assertFalse(app.query_one("#next", Button).display)
                    self.assertEqual(len(app.query("#workflow .workflow-step")), 2)
                    app._confirm_stage(2, False)
                    app._start(4, False)
                    app._start(1, True)
                    app.sequence_pressed()
                    app.next_pressed()
                    self.assertFalse(app.busy)
                    await pilot.pause()
                spawn.assert_not_called()

    async def test_macos_constructor_and_cli_reject_paid_stages(self):
        from tui import GoogleAITUI, main
        with tempfile.TemporaryDirectory() as temp:
            with patch("tui.is_macos_platform", return_value=True):
                for step in (2, 3, 4, 5):
                    with self.assertRaises(ValueError):
                        GoogleAITUI(repo=Path(temp), selected_step=step)
                with self.assertRaises(ValueError):
                    GoogleAITUI(repo=Path(temp), start_sequence=True)
                with self.assertRaises(SystemExit):
                    main(["--step", "2"])
                with self.assertRaises(SystemExit):
                    main(["--sequence"])


if __name__ == "__main__":
    unittest.main()
