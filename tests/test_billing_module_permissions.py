"""Offline regression tests for billing-module setup and safe failure reporting."""
import base64
import io
import unittest
from pathlib import Path
from unittest.mock import patch

import ultra0


class BillingModulePermissionTests(unittest.TestCase):
    def _run(self, existing=True, normal="ok", fallback="ok", push_error=None):
        calls = []
        def shell(*args, **kwargs):
            command = " ".join(str(a) for a in args)
            calls.append(command)
            if command.startswith("shell ls "):
                return ultra0.MODULE_REMOTE if existing else ""
            if command.startswith("push "):
                self.assertTrue(Path(args[1]).is_file())
                self.assertTrue(kwargs["check"])
                if push_error:
                    raise push_error
            if command.startswith("shell chmod "):
                if isinstance(normal, Exception):
                    raise normal
                return normal
            if command.startswith("shell su -c "):
                if isinstance(fallback, Exception):
                    raise fallback
                return fallback
            return ""
        with patch.object(ultra0, "sh", side_effect=shell), \
             patch.object(ultra0, "MODULE_B64", base64.b64encode(b"test").decode()):
            ultra0.ensure_module_apk()
        return calls

    def test_existing_module_is_normalized(self):
        calls = self._run()
        self.assertTrue(any(c.startswith("shell chmod 644 ") for c in calls))
        self.assertFalse(any(c.startswith("push ") for c in calls))

    def test_new_module_is_pushed_before_permission_check(self):
        calls = self._run(existing=False)
        self.assertLess(next(i for i,c in enumerate(calls) if c.startswith("push ")),
                        next(i for i,c in enumerate(calls) if c.startswith("shell chmod ")))

    def test_authorized_root_fallback(self):
        calls = self._run(normal=RuntimeError("permission denied"))
        self.assertTrue(any(c.startswith("shell su -c ") for c in calls))

    def test_permission_failure_stops_and_emits_safe_marker(self):
        with patch.object(ultra0.sys, "stdout", io.StringIO()) as output:
            with self.assertRaisesRegex(RuntimeError, "Billing module setup failed"):
                self._run(normal="", fallback=RuntimeError("private@example.com"))
        self.assertIn("EPLUS_ISSUE:billing_module_setup_failed", output.getvalue())
        self.assertNotIn("private@example.com", output.getvalue())

    def test_push_failure_stops(self):
        with self.assertRaisesRegex(RuntimeError, "Billing module setup failed"):
            self._run(existing=False, push_error=RuntimeError("push failed"))


class BillingModuleMessageTests(unittest.TestCase):
    def test_native_adapters_preserve_setup_failure(self):
        import macos_runner as adapter
        for env in ({}, {adapter.LINUX_WORKDIR: "/private"}):
            with self.subTest(linux=bool(env)):
                with patch.object(adapter.subprocess, "Popen") as popen, \
                     patch.object(ultra0.sys, "stdout", io.StringIO()) as output:
                    child = popen.return_value.__enter__.return_value
                    child.stdout = iter(["EPLUS_ISSUE:billing_module_setup_failed\n"])
                    child.wait.return_value = 1
                    with self.assertRaisesRegex(RuntimeError, "^Billing module setup failed$"):
                        adapter.run_engine(["python"], env)
                self.assertNotIn("Android stage failed", output.getvalue())

    def test_dashboard_classifies_setup_failure(self):
        from tui_core import cli_issue_outcome, runtime_error_outcome
        for outcome in (
            cli_issue_outcome(["EPLUS_ISSUE:billing_module_setup_failed"], 1),
            runtime_error_outcome("Billing module setup failed", 1),
        ):
            self.assertEqual(outcome.code, "billing_module_setup_failed")
            self.assertFalse(outcome.can_review)
            self.assertIn("permissions", outcome.instruction)


if __name__ == "__main__":
    unittest.main()
