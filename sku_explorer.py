"""Read-only SKU Explorer modal shared by the app and real TUI screenshot CI.

The modal only executes sku_check_runner.py, a separate query-only process.
It cannot launch a paid step, generate a checkout or change an account.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from textual import on, work
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static

from sku_check_core import render_result, validate_skus

ROOT = Path(__file__).resolve().parent


class SKUExplorer(ModalScreen[None]):
    """Explicit single-SKU check, never a checkout action."""

    CSS = """
    SKUExplorer { align: center middle; background: #071526 88%; }
    #sku_card {
        width: 105; max-width: 96%; height: auto; max-height: 97%;
        background: #10253d; border: round #3c97b8; padding: 0 2;
    }
    #sku_title { color: #b4eafa; text-style: bold; }
    #sku_notice { color: #9bc5d9; height: auto; }
    #sku_groups { height: 3; margin-top: 0; }
    #sku_groups Button { width: 1fr; margin-right: 1; }
    #sku_pro { background: #24577a; color: #f7fbff; }
    #sku_input { width: 100%; margin-top: 0; }
    #sku_commands { height: 3; margin-top: 0; }
    #sku_commands Button { margin-right: 1; }
    #sku_check { width: 25; }
    #sku_cancel { width: 15; }
    #sku_clear { width: 13; }
    #sku_results {
        height: 6; min-height: 5; max-height: 8;
        border: round #365c7b; background: #0a1b30;
        margin-top: 0; padding: 0 1; overflow-y: auto;
    }
    #sku_output { color: #deedf9; height: auto; }
    #sku_warning { color: #9dcce0; height: auto; margin-top: 0; }
    #sku_close { width: 27; height: 3; margin-top: 0; }
    Screen.compact #sku_card { padding: 0 1; }
    Screen.compact #sku_results { height: 5; }
    """

    def __init__(self, *, serial: str | None = None, preview: bool = False) -> None:
        super().__init__()
        self.serial = serial if serial else None
        self.preview = preview
        self._running = False
        self._process: subprocess.Popen[str] | None = None

    def compose(self):
        with Vertical(id="sku_card"):
            yield Static("STEP 1  /  SKU EXPLORER  /  READ-ONLY CHECK SKU", id="sku_title")
            yield Static(
                "SIMULATED DATA ONLY  •  No device/account/checkout."
                if self.preview else
                ("Device from Step 1 verified; metadata only, no checkout."
                 if self.serial else
                 "Run Check Device & Offers (Step 1) first to verify your device/account."),
                id="sku_notice",
            )
            with Horizontal(id="sku_groups"):
                yield Button("AI Pro", id="sku_pro")
                yield Button("Ultra", id="sku_ultra")
                yield Button("Custom", id="sku_custom")
            yield Input(value="g1.2tb.ai.subs_variant", placeholder="Google Play product ID",
                        id="sku_input")
            with Horizontal(id="sku_commands"):
                yield Button("Check SKU (read-only)", id="sku_check", variant="success",
                             disabled=self.preview or not self.serial)
                yield Button("Cancel check", id="sku_cancel", disabled=True)
                yield Button("Clear", id="sku_clear")
            with VerticalScroll(id="sku_results"):
                yield Static(
                    "PREVIEW RESULT  •  OBSERVED (SIMULATED)\n"
                    "Product ID: g1.example.pro\n"
                    "Offer ID: example-offer\n"
                    "Phase 1: 0.00 USD / P1M\n"
                    "Phase 2: 19.99 USD / P1M\n"
                    "Eligibility: UNVERIFIED\n"
                    "NO CHECKOUT • No payment was attempted"
                    if self.preview else
                    "No SKU check has been run.\n"
                    "A returned SKU is NOT proof of eligibility, activation or free months.",
                    id="sku_output",
                )
            yield Static(
                "NO CHECKOUT  •  No token, account switch or payment. Pricing terms are not verified.",
                id="sku_warning",
            )
            yield Button("Close SKU Explorer", id="sku_close")

    @on(Button.Pressed, "#sku_groups Button")
    def select_group(self, event: Button.Pressed) -> None:
        if self._running:
            return
        value = {
            "sku_pro": "g1.2tb.ai.subs_variant",
            "sku_ultra": "g1.play.20tb",
            "sku_custom": "",
        }.get(event.button.id, "")
        self.query_one("#sku_input", Input).value = value

    @on(Button.Pressed, "#sku_clear")
    def clear_sku(self) -> None:
        if not self._running:
            self.query_one("#sku_input", Input).value = ""

    @on(Button.Pressed, "#sku_check")
    def check_sku(self) -> None:
        if self.preview or self._running or not self.serial:
            return
        value = self.query_one("#sku_input", Input).value.strip()
        try:
            validate_skus([value])
        except ValueError:
            self.query_one("#sku_output", Static).update(
                "Invalid SKU. Enter an explicit product ID starting with g1.")
            return
        self._running = True
        self.query_one("#sku_check", Button).disabled = True
        self.query_one("#sku_clear", Button).disabled = True
        self.query_one("#sku_cancel", Button).disabled = False
        self.query_one("#sku_output", Static).update(
            "Checking Google Play ProductDetails for the selected SKU...\n"
            "Read-only query; no checkout will be opened.")
        self.run_readonly_query(self.serial, value)

    @work(thread=True, exclusive=True, group="sku-readonly")
    def run_readonly_query(self, serial: str, sku: str) -> None:
        result: dict = {"status": "query_error"}
        try:
            cmd = [
                sys.executable, str(ROOT / "sku_check_runner.py"),
                "--serial", serial, "--sku", sku,
            ]
            proc = subprocess.Popen(
                cmd, cwd=ROOT, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
                errors="replace",
            )
            self._process = proc
            try:
                output, _ = proc.communicate(timeout=36)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                result = {"status": "timeout"}
            else:
                if len(output) <= 200_000:
                    loaded = json.loads(output)
                    if isinstance(loaded, dict) and isinstance(loaded.get("items", []), list):
                        # Renderer uses only whitelisted fields from the runner.
                        result = loaded
        except (OSError, ValueError, UnicodeError, json.JSONDecodeError):
            result = {"status": "query_error"}
        finally:
            self._process = None
        try:
            self.app.call_from_thread(self.query_finished, result)
        except Exception:
            pass  # The modal may have been closed during cancellation.

    def query_finished(self, result: dict) -> None:
        if not self.is_mounted:
            return
        self._running = False
        self.query_one("#sku_check", Button).disabled = self.preview or not self.serial
        self.query_one("#sku_clear", Button).disabled = False
        self.query_one("#sku_cancel", Button).disabled = True
        try:
            message = render_result(result)
        except (ValueError, TypeError, KeyError, ArithmeticError):
            message = "The read-only SKU result could not be displayed safely."
        self.query_one("#sku_output", Static).update(message)

    @on(Button.Pressed, "#sku_cancel")
    def cancel_check(self) -> None:
        if not self._running:
            return
        proc = self._process
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                pass
        self.query_one("#sku_output", Static).update("Cancelling read-only SKU check...")

    @on(Button.Pressed, "#sku_close")
    def close_sku(self) -> None:
        self.cancel_check()
        self.dismiss(None)

    def on_unmount(self) -> None:
        proc = self._process
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                pass
