#!/usr/bin/env python3
"""Render real TUI screens with synthetic, non-transactional fixture states."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tui import GoogleAITUI  # noqa: E402
from tui_core import Outcome  # noqa: E402
from device_diagnostics import ConnectionStatus  # noqa: E402
from textual.widgets import Button  # noqa: E402
from sku_explorer import SKUExplorer  # noqa: E402
from offer_discovery import parse_step1  # noqa: E402

SCENARIOS = {"startup", "disconnected", "offer_found", "step_picker", "approval", "review",
             "linux_startup", "linux_step_picker", "sku_explorer", "sku_step",
             "sku_extra_steps"}
scenario = os.environ.get("PREVIEW_SCENARIO", "")
if scenario not in SCENARIOS:
    raise SystemExit("Invalid preview scenario")


class PreviewApp(GoogleAITUI):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Synthetic states; never invoke real Android/Google Play operations.
        # Linux scenarios explicitly activate the native Linux UI path.
        self.linux_mode = scenario.startswith("linux_")
        self.macos_mode = False
        self.native_mode = self.linux_mode

    def _poll_connection(self):
        pass  # Never probe host devices from a screenshot run.

    def run_stage(self, step):
        raise RuntimeError("Real stages are disabled in terminal previews")

    def on_mount(self):
        super().on_mount()
        self.set_timer(0.5, self.prepare_scenario)

    def prepare_scenario(self):
        if scenario in {"startup", "linux_startup"}:
            return
        if scenario == "sku_explorer":
            self.push_screen(SKUExplorer(preview=True))
            return
        if scenario == "sku_step":
            # Show Check SKU directly alongside the Step 1 offer check.
            self.query_one("#sku_explorer", Button).focus()
            return
        if scenario == "sku_extra_steps":
            self._update_discovered(parse_step1({"offers": [
                {"product": "g1.2tb.ai.subs_variant", "id": "12months-eft", "micros": "0"},
                {"product": "g1.2tb.ai.subs_variant", "id": "6months-eft-ss-2026", "micros": "0"},
                {"product": "g1.play.20tb", "id": "promo-2026", "micros": "19990000"},
            ]}))
            return
        if scenario == "disconnected":
            self._connection_polled(ConnectionStatus("disconnected"))
        elif scenario == "offer_found":
            # The synthetic successful check needs the same device identity
            # that the real Step 1 status output supplies.
            self._received("Device emulator-5554")
            self._verified_account = "preview@example.invalid"
            self._finished(1, Outcome("listed", "Offers loaded", "Review offers"), {
                "status": "listed", "detected_play_account": "preview@example.invalid",
                "offers": [{"id": "12months-eft", "micros": "0", "period": "P1Y"}],
            })
        elif scenario in {"step_picker", "linux_step_picker"}:
            self.advanced_pressed()
        elif scenario == "approval":
            self._offer_check_ready = True
            self._confirm_stage(2, True)
        elif scenario == "review":
            self._offer_check_ready = True
            self.sequence = True
            self.current_step = 2
            self._finished(2, Outcome("checkout_requested", "Checkout submitted - not yet verified",
                                     "Check Google Play subscriptions and renewal date.", True), {})


PreviewApp(repo=Path(__file__).resolve().parents[2]).run()
