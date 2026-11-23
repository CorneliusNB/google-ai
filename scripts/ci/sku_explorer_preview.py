"""SKU Explorer UI prototype rendered in the real Textual preview harness.

Synthetic display only: no network, ADB, Frida, Google account, checkout,
purchase-token lookup, or access to runtime reports. Not production UI.
"""
from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static


class SKUExplorerPreview(ModalScreen[None]):
    """Click-through UI concept for Check SKU; never runs real billing logic."""

    CSS = """
    SKUExplorerPreview {
        align: center middle;
        background: #061323 88%;
    }
    #sku_card {
        width: 100;
        max-width: 97%;
        height: auto;
        max-height: 96%;
        background: #10243c;
        border: round #4f9cc0;
        padding: 0 2;
    }
    #sku_header { height: 1; color: #eaf6ff; text-style: bold; }
    #sku_note { height: auto; color: #91c8e3; margin: 0; }
    #sku_toolbar { height: 3; margin: 0; }
    #sku_toolbar Button { width: 1fr; margin-right: 1; }
    #sku_toolbar #sku_pro { background: #205779; color: #f1faff; }
    #sku_toolbar #sku_ultra, #sku_toolbar #sku_custom {
        background: #192f49; color: #c3d8ea;
    }
    #sku_form { height: 3; margin: 0; }
    #sku_form Input { width: 1fr; background: #081a2d; color: #f3f9ff; }
    #sku_actions { height: 3; margin: 0; }
    #sku_actions Button { margin-right: 1; }
    #sku_check { width: 23; background: #275c73; color: #ffffff; }
    #sku_clear { width: 12; }
    #sku_result {
        min-height: 9; height: 9; max-height: 9;
        border: round #336a88;
        background: #0a1b30; padding: 0 1;
    }
    #sku_result_title { color: #a7e5fa; text-style: bold; }
    #sku_rows { color: #dae8f6; height: auto; }
    #sku_detail { color: #a9c7d8; height: auto; margin-top: 1; }
    #sku_footer { height: auto; color: #98c0d7; margin-top: 0; }
    #sku_close { width: 19; height: 2; margin-top: 0; background: #203d59; }
    Screen.tiny #sku_card { padding: 0 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="sku_card"):
            yield Static("STEP 1  /  SKU EXPLORER  /  READ-ONLY PREVIEW", id="sku_header")
            yield Static(
                "SIMULATED DATA ONLY  •  No Google Play lookup, account access or checkout.",
                id="sku_note",
            )
            with Horizontal(id="sku_toolbar"):
                yield Button("AI Pro", id="sku_pro")
                yield Button("Ultra", id="sku_ultra")
                yield Button("Custom", id="sku_custom")
            with Horizontal(id="sku_form"):
                yield Input(
                    value="g1.example.pro",
                    placeholder="Enter a Google Play Product ID (SKU)",
                    id="sku_input",
                )
            with Horizontal(id="sku_actions"):
                yield Button("Check SKU  (preview)", id="sku_check", disabled=True)
                yield Button("Clear", id="sku_clear")
            with VerticalScroll(id="sku_result"):
                yield Static("PREVIEW RESULT  •  OBSERVED (SIMULATED)", id="sku_result_title")
                yield Static(
                    "Product ID         Offer ID           First phase         Renewal\n"
                    "g1.example.pro     example-offer      USD 0 / P1M         USD 19.99 / P1M\n"
                    "g1.example.ultra   example-discount   USD 1.99 / P1M      Unknown",
                    id="sku_rows",
                )
                yield Static(
                    "Details: billing period / cycle count / currency / recurrence are "
                    "shown only when returned by an actual product-details query.",
                    id="sku_detail",
                )
            yield Static(
                "Eligibility: UNVERIFIED  |  Subscription active: UNVERIFIED\n"
                "NO CHECKOUT  •  No billing-sheet launch  •  No tokens saved or displayed",
                id="sku_footer",
            )
            yield Button("Close preview", id="sku_close")

    @on(Button.Pressed, "#sku_close")
    def close_preview(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#sku_clear")
    def clear_sku(self) -> None:
        self.query_one("#sku_input", Input).value = ""

    @on(Button.Pressed, "#sku_toolbar Button")
    def select_group(self, event: Button.Pressed) -> None:
        candidate = {
            "sku_pro": "g1.example.pro",
            "sku_ultra": "g1.example.ultra",
            "sku_custom": "",
        }[event.button.id]
        self.query_one("#sku_input", Input).value = candidate
