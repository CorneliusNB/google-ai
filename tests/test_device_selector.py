"""Unit tests for automatic ADB serial selection (no real Android needed)."""
import subprocess
import unittest
from unittest.mock import patch
import device_selector as selector

A = "127.0.0.1:16384"
B = "127.0.0.1:7555"
C = "emulator-5554"
BOOT_A = "11111111-2222-3333-4444-555555555555"
BOOT_B = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


class SelectionTests(unittest.TestCase):
    def test_adb_command_uses_requested_timeout(self):
        with patch.object(selector.subprocess, "run") as run:
            selector.adb_command("adb", "devices")
            self.assertEqual(run.call_args.kwargs["timeout"], 8)
            selector.adb_command("adb", "shell", "am", "start", timeout=20)
            self.assertEqual(run.call_args.kwargs["timeout"], 20)
            run.side_effect = subprocess.TimeoutExpired("adb", 20)
            self.assertIsNone(selector.adb_command("adb", "devices", timeout=20))

    def test_online_serials_keeps_legacy_empty_list_on_failure(self):
        with patch.object(selector, "adb_command", return_value=None):
            self.assertEqual(selector.online_serials("adb"), [])
            self.assertIsNone(selector.online_serials("adb", distinguish_failure=True))

    def test_only_device(self):
        self.assertEqual(selector.auto_select_device("adb", serials=[C]), C)

    def test_explicit_choice(self):
        self.assertEqual(selector.auto_select_device("adb", preferred=B, serials=[A, B]), B)
        self.assertIsNone(selector.auto_select_device("adb", preferred=C, serials=[A, B]))

    def test_deduplicate_three_transports_with_same_boot_id(self):
        with patch.object(selector, "boot_uuid", return_value=BOOT_A):
            self.assertEqual(selector.auto_select_device("adb", serials=[A, B, C]), C)

    def test_unique_active_google_one(self):
        with patch.object(selector, "boot_uuid", side_effect=lambda adb, s: BOOT_A if s == A else BOOT_B), \
             patch.object(selector, "running_google_one", side_effect=lambda adb, s: s == B):
            self.assertEqual(selector.auto_select_device("adb", serials=[A, B]), B)

    def test_unique_installed_google_one(self):
        with patch.object(selector, "boot_uuid", return_value=""), \
             patch.object(selector, "running_google_one", return_value=False), \
             patch.object(selector, "installed_google_one", side_effect=lambda adb, s: s == A):
            self.assertEqual(selector.auto_select_device("adb", serials=[A, B]), A)

    def test_ambiguous_distinct_devices_stop(self):
        with patch.object(selector, "boot_uuid", return_value=""), \
             patch.object(selector, "running_google_one", return_value=True):
            self.assertIsNone(selector.auto_select_device("adb", serials=[A, B]))

    def test_no_boot_id_not_assumed_duplicate(self):
        with patch.object(selector, "boot_uuid", return_value=""), \
             patch.object(selector, "running_google_one", return_value=False), \
             patch.object(selector, "installed_google_one", return_value=False):
            self.assertIsNone(selector.auto_select_device("adb", serials=[A, B]))

    def test_invalid_boot_id(self):
        class Result:
            returncode = 0
            stdout = "unknown\n"
        with patch.object(selector, "adb_command", return_value=Result()):
            self.assertEqual(selector.boot_uuid("adb", A), "")


if __name__ == "__main__":
    unittest.main()
