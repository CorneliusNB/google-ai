"""Interactive Textual frontend for the existing Google AI MuMu PowerShell CLI.

UI-only orchestration: the original run-all.ps1 and ultra0.py still own all
Android, Frida, Google Play, payment and account validation. The TUI never
declares an activated subscription from launchBillingFlow or a Subscribe tap.
"""
from __future__ import annotations

import argparse
import os
from collections import deque
from pathlib import Path
import re
import subprocess
import sys
import time

from rich.markup import escape
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, RichLog, Select, Static

from tui_core import STAGES, Outcome, command_for_step, mask_email, \
    needs_setup, outcome_for_stage, read_fresh_report, report_summary, validate_step


class Approval(ModalScreen[bool]):
    """Clickable approval without long typed phrases."""

    CSS = """
    Approval { align: center middle; background: #070d19 75%; }
    #approval_card {
        width: 66; max-width: 92%; height: auto;
        padding: 2 3; background: #15243a; border: round #3d6383;
    }
    #approval_title { text-style: bold; color: #ebf5ff; margin-bottom: 1; }
    #approval_message { color: #c9d8e8; margin-bottom: 2; }
    #approval_actions { height: auto; align-horizontal: right; }
    #approval_actions Button { margin-left: 1; }
    """

    def __init__(self, title: str, message: str) -> None:
        super().__init__()
        self.title_text, self.message_text = title, message

    def compose(self) -> ComposeResult:
        with Vertical(id="approval_card"):
            yield Static(self.title_text, id="approval_title")
            yield Static(self.message_text, id="approval_message")
            with Horizontal(id="approval_actions"):
                yield Button("Cancel", id="cancel")
                yield Button("Continue", id="approve", variant="warning")

    @on(Button.Pressed, "#approval_actions Button")
    def approve(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "approve")


class GoogleAITUI(App[None]):
    TITLE = "Google AI | ePlus.DEV"
    SUB_TITLE = "MuMu toolkit"
    BINDINGS = [
        ("d", "toggle_debug", "Debug"),
        ("r", "run_selected", "Run step"),
        ("q", "quit_safely", "Quit"),
    ]
    CSS = """
    Screen { background: #0b1220; color: #d9e8f6; }
    Header { background: #172741; color: #dbeeff; }
    Footer { background: #172741; color: #c6d9ee; }
    #screen { height: 1fr; min-height: 0; padding: 0 1; }
    #brand {
        height: 3; padding: 0 1; color: #ecf8ff; text-style: bold;
        background: #15283e; border: solid #2f5c79;
    }
    #credit { color: #8db6ce; margin: 0; height: 1; }
    #details { height: 1; margin-bottom: 1; }
    #device, #account { width: 1fr; padding: 0 1; background: #142238; }
    #content { height: 1fr; min-height: 0; }
    #controls {
        width: 37; min-width: 28; min-height: 0; overflow-y: auto;
        border: round #35536e; background: #111f32; padding: 0 1;
    }
    #results {
        width: 1fr; min-width: 24; min-height: 0; overflow-y: auto;
        border: round #35536e; background: #111f32; padding: 0 1; margin-left: 1;
    }
    .section { color: #78cfe8; text-style: bold; margin: 1 0 0 0; }
    #step { margin-bottom: 0; }
    #controls Button { width: 100%; margin-bottom: 0; }
    #quickstart { margin: 1 0; }
    #advanced_label { color: #78cfe8; margin-top: 1; }
    #advanced { display: none; height: auto; }
    #advanced Button { margin-bottom: 0; }
    #elapsed, #activity { color: #9dbcd2; }
    #quick_hint { margin-bottom: 1; }
    #debug_log { display: none; height: 9; border: solid #29465e; }
    #controls { scrollbar-size: 1 1; }
    #state { color: #f3f8ff; text-style: bold; margin: 1 0 0 0; }
    #message { color: #b9d0e2; margin-bottom: 1; }
    #step_result { color: #8dd6b7; margin: 1 0; }
    #manual { display: none; margin: 1 0; }
    #debug_log { display: none; height: 1fr; border: solid #29465e; }
    #hint { color: #91adc0; margin-top: 1; }
    """

    def __init__(self, *, repo: Path, selected_step: int = 1,
                 start_sequence: bool = False, initial_debug: bool = False) -> None:
        super().__init__()
        self.repo = repo.resolve()
        self.initial_step = validate_step(selected_step)
        self.start_sequence = start_sequence
        self.debug_visible = initial_debug
        self.busy = False
        self.sequence = False
        self.current_step: int | None = None
        self._child: subprocess.Popen[str] | None = None
        self._last_output: deque[str] = deque(maxlen=350)
        self._run_output: deque[str] = deque(maxlen=35)
        self._stop_after_step = False
        self._last_outcome: Outcome | None = None
        self._started_at: float | None = None
        self._last_activity_at: float | None = None
        self.advanced_visible = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="screen"):
            yield Static("  GOOGLE AI  /  MuMu Toolkit", id="brand")
            yield Static("  Original @gylive   |   Maintained @hoangsvit   |   https://eplus.dev", id="credit")
            with Horizontal(id="details"):
                yield Static("Device  •  Auto-detect", id="device")
                yield Static("Account  •  Waiting", id="account")
            with Horizontal(id="content"):
                with Vertical(id="controls"):
                    yield Static("WELCOME", classes="section")
                    yield Static("Check your Google AI offers. Start below.", id="welcome")
                    yield Button("Check device & offers", id="quickstart", variant="success")
                    yield Static("Read-only: no subscription or payment is initiated.", id="quick_hint")
                    yield Button("Advanced options  +", id="advanced_toggle")
                    with Vertical(id="advanced"):
                        yield Static("CHOOSE A STEP", id="advanced_label", classes="section")
                        yield Select(
                            [(f"{stage.number}  ·  {stage.label}", stage.number) for stage in STAGES],
                            value=self.initial_step, id="step", allow_blank=False)
                        yield Button("Run selected step", id="run")
                        yield Button("Run sequence from selected step", id="sequence")
                    yield Button("Verified in Google Play → Next", id="next", disabled=True)
                    yield Button("Stop after this step", id="stop", disabled=True)
                    yield Button("Show technical details", id="debug")
                with Vertical(id="results"):
                    yield Static("CURRENT STATUS", classes="section")
                    yield Static("Ready — no check started", id="state")
                    yield Static("Click Check device & offers on the left to begin.", id="message")
                    yield Static("", id="step_result")
                    yield Static("Elapsed: --", id="elapsed")
                    yield Static("Nothing is running.", id="activity")
                    yield Button("Completed action on Android", id="manual", disabled=True)
                    yield Static("Steps 2–5 may open real Google Play checkout. "
                                 "A checkout request is not proof of activation.", id="hint")
                    yield RichLog(id="debug_log", wrap=True, highlight=False, markup=False)
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(1, self._refresh_elapsed)
        self.query_one("#debug_log", RichLog).display = self.debug_visible
        self.query_one("#debug", Button).label = "Hide technical details" if self.debug_visible else "Show technical details"
        if self.start_sequence:
            self.action_toggle_advanced()
            self._set_message("Sequence mode selected. Review the starting step, then click Run sequence.")

    @on(Button.Pressed, "#advanced_toggle")
    def advanced_pressed(self) -> None:
        self.action_toggle_advanced()

    def action_toggle_advanced(self) -> None:
        self.advanced_visible = not self.advanced_visible
        self.query_one("#advanced", Vertical).display = self.advanced_visible
        self.query_one("#advanced_toggle", Button).label = (
            "Advanced options  -" if self.advanced_visible else "Advanced options  +"
        )

    def _refresh_elapsed(self) -> None:
        if not self.busy or self._started_at is None:
            return
        elapsed = int(time.monotonic() - self._started_at)
        self.query_one("#elapsed", Static).update(f"Elapsed: {elapsed // 60:02d}:{elapsed % 60:02d}")
        if self._last_activity_at is not None:
            idle = int(time.monotonic() - self._last_activity_at)
            if idle >= 30:
                self.query_one("#activity", Static).update(
                    f"No new output for {idle}s. Check MuMu or technical details."
                )

    def _set_message(self, value: str) -> None:
        self.query_one("#message", Static).update(value)

    def _set_status(self, value: str) -> None:
        self.query_one("#state", Static).update(value)

    def _selected(self) -> int:
        return validate_step(int(self.query_one("#step", Select).value))

    def _confirm_stage(self, step: int, sequence: bool,
                       previous_verified: bool = False) -> None:
        if self.busy:
            return
        if step == 2:
            title = "Start initial 12-month checkout?"
            message = ("Confirm this Google Play account has NO active Google One subscription. "
                       "This step can automatically press Subscribe and create real charges.")
        elif step >= 3:
            title = f"Start Step {step} (+6 months)?"
            message = ("Google AI Pro must already be active. Verify the previous "
                       "subscription and renewal date in Google Play. Google may reject "
                       "additional free offers or apply paid renewal terms.")
        else:
            self._start(step, sequence)
            return
        if previous_verified:
            message = ("Confirm the previous stage ACTUALLY changed the Google Play "
                       "subscription/renewal date. " + message)
        self.push_screen(Approval(title, message),
                         lambda approved: self._start(step, sequence) if approved else None)

    @on(Button.Pressed, "#quickstart")
    def quickstart_pressed(self) -> None:
        self._confirm_stage(1, False)

    @on(Button.Pressed, "#run")
    def selected_pressed(self) -> None:
        self._confirm_stage(self._selected(), False)

    @on(Button.Pressed, "#sequence")
    def sequence_pressed(self) -> None:
        step = self._selected()
        if step < 2:
            self._set_message("Choose Step 2, 3, 4 or 5 to start the subscription sequence.")
            return
        self._confirm_stage(step, True)

    @on(Button.Pressed, "#next")
    def next_pressed(self) -> None:
        if self.busy or not self.sequence or self.current_step is None:
            return
        if self._last_outcome is None or not self._last_outcome.can_review:
            return
        next_step = self.current_step + 1
        if next_step > 5:
            return
        self._confirm_stage(next_step, True, previous_verified=True)

    @on(Button.Pressed, "#stop")
    def stop_pressed(self) -> None:
        # Terminating an in-flight Play checkout can leave its result unknown.
        # Do not kill the subprocess during a billing operation.
        self._stop_after_step = True
        self._set_message("Will stop after this step. Check Google Play before restarting.")

    @on(Button.Pressed, "#manual")
    def manual_pressed(self) -> None:
        child = self._child
        if child and child.stdin:
            try:
                child.stdin.write("\n")
                child.stdin.flush()
                self.query_one("#manual", Button).disabled = True
                self.query_one("#manual", Button).display = False
            except (OSError, ValueError):
                self._set_message("Could not continue the Android prompt. See Debug.")

    @on(Button.Pressed, "#debug")
    def debug_pressed(self) -> None:
        self.action_toggle_debug()

    def action_toggle_debug(self) -> None:
        self.debug_visible = not self.debug_visible
        log = self.query_one("#debug_log", RichLog)
        log.display = self.debug_visible
        self.query_one("#debug", Button).label = "Hide Debug" if self.debug_visible else "Show Debug"
        if self.debug_visible and not getattr(self, "_debug_loaded", False):
            for line in self._last_output:
                log.write(line)
            self._debug_loaded = True

    def action_run_selected(self) -> None:
        self._confirm_stage(self._selected(), False)

    def action_quit_safely(self) -> None:
        if self.busy:
            self._set_message("A step is running. Wait for it to finish; do not interrupt checkout.")
        else:
            self.exit()

    def _start(self, step: int, sequence: bool) -> None:
        if self.busy:
            return
        self.busy = True
        self.sequence = sequence
        self.current_step = step
        self._stop_after_step = False
        self._last_outcome = None
        self._run_output.clear()
        self._started_at = time.monotonic()
        self._last_activity_at = self._started_at
        self.query_one("#elapsed", Static).update("Elapsed: 00:00")
        self.query_one("#activity", Static).update("Connecting to MuMu and preparing tools...")
        self.query_one("#quickstart", Button).disabled = True
        self.query_one("#run", Button).disabled = True
        self.query_one("#sequence", Button).disabled = True
        self.query_one("#step", Select).disabled = True
        self.query_one("#next", Button).disabled = True
        self.query_one("#stop", Button).disabled = False
        self.query_one("#step_result", Static).update(f"Step {step} · {STAGES[step].label}")
        self._set_status("Running — check MuMu if prompted")
        self._set_message("Preparing tools and checking Google Play. Missing dependencies are installed automatically.")
        self.run_stage(step)

    def _execute(self, command: list[str]) -> int:
        """Run the existing engine and send output to the TUI without blocking it."""
        # Windows Python defaults to a locale code page when stdout is piped.
        # Force UTF-8 for nested setup/CLI Python processes without changing billing logic.
        child_env = os.environ.copy()
        child_env["PYTHONIOENCODING"] = "utf-8"
        child_env["PYTHONUTF8"] = "1"
        with subprocess.Popen(
            command, cwd=self.repo, env=child_env, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, stdin=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", bufsize=1
        ) as child:
            self._child = child
            if child.stdout:
                for line in child.stdout:
                    try:
                        self.call_from_thread(self._received, line.rstrip("\r\n"))
                    except RuntimeError:
                        return -1
            return child.wait()

    @work(thread=True, exclusive=True)
    def run_stage(self, step: int) -> None:
        try:
            if needs_setup():
                self.call_from_thread(self._set_status, "Setting up...")
                self.call_from_thread(self._set_message,
                                      "Preparing Frida and ADB. You do not need a separate setup command.")
                setup = self.repo / "setup_env.py"
                if not setup.is_file():
                    raise FileNotFoundError("setup_env.py is missing from the project directory")
                if self._execute([sys.executable, str(setup)]) != 0:
                    self.call_from_thread(
                        self._finished, step,
                        Outcome("setup_failed", "Setup did not finish",
                                "Open Debug, check the setup issue, then retry. No checkout was started."),
                        None)
                    return

            # Never treat a report from setup or a previous invocation as the
            # outcome of the selected step.
            started = time.time()
            command = command_for_step(step, self.repo)
            return_code = self._execute(command)
            report = read_fresh_report(self.repo / "ultra0-report", step, started)
            result = outcome_for_stage(step, return_code, report)
            self.call_from_thread(self._finished, step, result, report)
        except Exception as error:
            result = Outcome("exception", "Could not start the tool",
                             f"{type(error).__name__}: {error}. See Debug and verify Google Play.")
            self.call_from_thread(self._finished, step, result, None)
        finally:
            self._child = None

    def _received(self, line: str) -> None:
        if not line:
            return
        self._last_output.append(line)
        self._run_output.append(line)
        self._last_activity_at = time.monotonic()
        lower = line.lower()
        if "frida" in lower or "setup" in lower:
            phase = "Preparing Android tools..."
        elif "adb" in lower or "device" in lower:
            phase = "Checking Android device..."
        elif "offer" in lower or "billing" in lower or "google one" in lower:
            phase = "Checking available offers..."
        elif "account" in lower or "play store" in lower:
            phase = "Checking Google Play account..."
        else:
            phase = "Process responding. Details available in technical log."
        self.query_one("#activity", Static).update(phase)
        if self.debug_visible:
            self.query_one("#debug_log", RichLog).write(line)
        if re.search(r"Action required:|Press Enter to continue", line, re.I):
            btn = self.query_one("#manual", Button)
            btn.display = True
            btn.disabled = False
            self._set_message("Complete the requested action on Android, then click Completed.")
        if re.search(r"\bDevice\s+(emulator-\d+|[0-9.]+:\d+)\s*$", line):
            self.query_one("#device", Static).update("Device  •  " + escape(line.split()[-1]))
        if re.search(r"\bAccount\s+[^\s]+@[^\s]+", line):
            match = re.search(r"([^\s]+@[^\s]+)", line)
            if match:
                self.query_one("#account", Static).update("Account  •  " + escape(mask_email(match.group(1))))

    def _visible_failure(self) -> str:
        """Show a concise CLI error without exposing account emails."""
        for raw in reversed(self._run_output):
            line = re.sub(r"\x1b\[[0-9;]*m", "", raw).strip()
            if not line:
                continue
            if re.search(r"error|failed|missing|not found|cannot|unable|offline|unauthorized|issue|stopped|device", line, re.I):
                line = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[account hidden]", line)
                return line[:220]
        return ""

    def _finished(self, step: int, outcome: Outcome, report: dict | None) -> None:
        self.busy = False
        self._last_outcome = outcome
        self.query_one("#manual", Button).display = False
        self.query_one("#manual", Button).disabled = True
        self.query_one("#quickstart", Button).disabled = False
        self.query_one("#run", Button).disabled = False
        self.query_one("#sequence", Button).disabled = False
        self.query_one("#step", Select).disabled = False
        self.query_one("#stop", Button).disabled = True
        self._started_at = None
        self.query_one("#activity", Static).update("Step finished. Review the result above.")
        self._set_status(outcome.title)
        instruction = outcome.instruction
        if outcome.code in ("tool_error", "exception", "missing_report", "setup_failed"):
            diagnostic = self._visible_failure()
            if diagnostic:
                instruction = f"{instruction}  Last CLI message: {diagnostic}"
        self._set_message(instruction)
        if step == 1:
            self.query_one("#step_result", Static).update(report_summary(report))
        if outcome.can_review and self.sequence and step < 5 and not self._stop_after_step:
            self.query_one("#next", Button).disabled = False
        else:
            self.query_one("#next", Button).disabled = True
            self.sequence = False
        if outcome.code == "checkout_requested":
            self.notify("Review the actual subscription in Google Play.", severity="warning")
        elif outcome.code not in ("listed", "environment_ok"):
            self.notify("Step stopped; check the result before another attempt.", severity="warning")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Google AI MuMu Textual frontend")
    parser.add_argument("--step", type=int, default=1)
    parser.add_argument("--sequence", action="store_true")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args(argv)
    try:
        selected = validate_step(args.step)
    except ValueError as exc:
        parser.error(str(exc))
    GoogleAITUI(repo=Path(__file__).resolve().parent, selected_step=selected,
                start_sequence=args.sequence, initial_debug=args.debug).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
