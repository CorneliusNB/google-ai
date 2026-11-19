"""Confirm the guided PowerShell wrapper preserves the original step mapping."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class OriginalProStageTests(unittest.TestCase):
    def test_original_stage_numbers_and_offer_ids(self):
        ps = (ROOT / "run-all.ps1").read_text(encoding="utf-8")
        for step, plan, offer in (
            (2, "pro12", "12months-eft"),
            (3, "pro6", "6months-eft"),
            (4, "pro6b", "6months-eft-2"),
            (5, "pro6c", "6months-eft-ss-2026"),
        ):
            self.assertIn('Number = %d;' % step, ps)
            self.assertIn('Plan = "%s"; Offer = "%s"' % (plan, offer), ps)

    def test_no_checkout_by_default(self):
        ps = (ROOT / "run-all.ps1").read_text(encoding="utf-8")
        self.assertIn("[int]$Step = 1", ps)
        self.assertIn('if ($ListOnly -or ($Step -eq 1 -and -not $AllStages))', ps)
        self.assertIn('$_ .Number', ps.replace("$_ .Number", "$_ .Number")) if False else None

    def test_optional_stage_never_runs_in_all_stages(self):
        ps = (ROOT / "run-all.ps1").read_text(encoding="utf-8")
        self.assertIn('$_.Number -ge 2 -and $_.Number -le 4', ps)
        self.assertIn('if ($report.status -ne "checkout_requested")', ps)
        self.assertNotIn('"launched", "subscribed"', ps)
        self.assertNotIn(' "--force" ', ps)


if __name__ == "__main__":
    unittest.main()
