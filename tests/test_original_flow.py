"""No-device Frida target selection and subscription state regression tests."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

source = Path(__file__).resolve().parents[1] / "ultra0.py"
spec = importlib.util.spec_from_file_location("original_flow_guardrails", source)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def mock_dev(device_id, name="com.google.android.apps.subscriptions.red"):
    device = MagicMock()
    device.id = device_id
    device.type = "usb"
    device.get_process.return_value = types.SimpleNamespace(name=name)
    return device


class OriginalFlowGuardrails(unittest.TestCase):
    def test_serial_match_takes_precedence(self):
        devices = [mock_dev("127.0.0.1:16384"), mock_dev("emulator-5554")]
        module = types.SimpleNamespace(get_device_manager=lambda: types.SimpleNamespace(
            enumerate_devices=lambda: devices))
        with patch.dict(sys.modules, {"frida": module}):
            self.assertIs(mod.get_target_frida_device(123, "emulator-5554"), devices[1])

    def test_different_frida_devices_do_not_default_to_first(self):
        devices = [mock_dev("device-a"), mock_dev("device-b")]
        module = types.SimpleNamespace(get_device_manager=lambda: types.SimpleNamespace(
            enumerate_devices=lambda: devices))
        with patch.dict(sys.modules, {"frida": module}):
            with self.assertRaisesRegex(RuntimeError, "Cannot map ADB serial"):
                mod.get_target_frida_device(123, "emulator-5554")

    def test_unrelated_process_pid_refuses_attach(self):
        device = mock_dev("emulator-5554", name="com.example.other.app")
        module = types.SimpleNamespace(get_device_manager=lambda: types.SimpleNamespace(
            enumerate_devices=lambda: [device]))
        with patch.dict(sys.modules, {"frida": module}):
            with self.assertRaisesRegex(RuntimeError, "not Google One"):
                mod.get_target_frida_device(123, "emulator-5554")

    def test_missing_purchase_token_has_distinct_failure(self):
        s, message = mod.diagnose_launch_failure(
            {"launched": None, "errors": [{"ev": "no_purchase"}]})
        self.assertEqual(s, "subscription_update_unavailable")
        self.assertIn("token", message)

    def test_checkout_launch_is_not_subscription_activation(self):
        with patch.object(mod, "launch_app", return_value=123), \
             patch.object(mod, "run_trial", return_value={
                 "offers": [], "launched": {"code": 0}, "errors": [],
                 "purchase": None}), \
             patch.object(mod, "confirm_zero", return_value={"confirmed": True}), \
             patch.object(mod, "verify", return_value="Google AI Pro subscription"):
            result = mod.process("current@device", add=False, list_only=True)
            self.assertEqual(result["status"], "listed")
        with patch.object(mod, "current_play_account", return_value="test@example.com"), \
             patch.object(mod, "launch_app", return_value=123), \
             patch.object(mod, "run_trial", return_value={
                 "offers": [], "launched": {"code": 0}, "errors": [],
                 "purchase": None}), \
             patch.object(mod, "confirm_zero", return_value={"confirmed": True}), \
             patch.object(mod, "verify", return_value="Google AI Pro subscription"):
            result = mod.process("test@example.com", add=False, no_switch=True)
        self.assertEqual(result["status"], "checkout_requested")


if __name__ == "__main__":
    unittest.main()
