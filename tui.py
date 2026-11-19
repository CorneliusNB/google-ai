"""Interactive Textual frontend for ePlus AI Toolkit (Windows/MuMu PowerShell CLI).

UI-only orchestration: the original run-all.ps1 and ultra0.py still own all
Android, Frida, Google Play, payment and account validation. The TUI never
declares an activated subscription from launchBillingFlow or a Subscribe tap.
"""
from __future__ import annotations

import argparse
import os
import signal
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
    TITLE = "ePlus AI Toolkit"
    SUB_TITLE = "ePlus.DEV"
    BINDINGS = [
        ("d", "toggle_debug", "Debug"),
        ("r", "run_selected", "Run step"),
        ("q", "quit_safely", "Quit"),
    ]
    CSS = """
    Screen { background: #081424; color: #e8f2fc; }
    Header, Footer { background: #11243e; color: #d7e8fa; }
    #screen { height: 1fr; min-height: 0; padding: 0 1; }
    #brand { height: 3; background: #122741; border: round #28628d; color: #f0f8ff; text-style: bold; padding: 0 2; }
    #credit { height: 1; color: #87b8d4; }
    #details { height: 3; margin-bottom: 1; }
    #device, #account { width: 1fr; height: 3; background: #12263d; border: round #295a7e; padding: 0 1; }
    #account { margin-left: 1; }
    #content { height: 1fr; min-height: 0; }
    #controls { width: 32; min-width: 27; min-height: 0; overflow-y: auto; scrollbar-size: 1 1; background: #101f35; border: round #2b5577; padding: 0 1; }
    #results { width: 1fr; min-width: 23; min-height: 0; background: #081424; margin-left: 1; }
    .section { color: #6cdbf8; text-style: bold; margin-top: 1; }
    #controls Button { width: 100%; margin: 0; height: 3; }
    #nav_home { background: #1a4e7e; }
    #advanced { display: none; height: auto; }
    #advanced_label { margin: 0; }
    #advanced Select { margin: 0; }
    #next, #stop { display: none; }
    #exit { width: 100%; height: 3; }
    #workflow { height: auto; margin-top: 1; border-top: solid #28506b; }
    .workflow-step { height: 1; color: #b4cbe0; }
    #welcome_panel { height: auto; border: round #2b97bc; background: #112b49; padding: 0 2; margin-bottom: 1; }
    #welcome { color: #91e3ff; text-style: bold; height: 1; margin-top: 1; }
    #quick_hint { color: #afcce3; height: auto; margin-bottom: 1; }
    #quickstart { width: 100%; height: 3; margin-bottom: 1; }
    #read_only { color: #81c6df; height: 1; }
    #status_panel { height: 1fr; min-height: 0; border: round #285a80; background: #101f35; padding: 0 1; }
    #state { color: #f2f9ff; text-style: bold; margin-top: 1; }
    #message { color: #c5ddee; }
    #step_result { color: #8cdfbb; }
    #elapsed, #activity { color: #95c4dd; }
    #debug_log { display: none; height: 1fr; min-height: 3; border: round #294b67; background: #071528; }
    #manual { display: none; width: 100%; height: 3; }
    #hint { color: #83b1cf; height: auto; margin-top: 1; }
    Screen.compact #brand { height: 1; border: none; padding: 0 1; }
    Screen.compact #credit, Screen.compact #workflow, Screen.compact #hint { display: none; }
    Screen.compact #details { height: 1; }
    Screen.compact #device, Screen.compact #account { height: 1; border: none; }
    Screen.compact #welcome_panel { padding: 0 1; }
    Screen.compact #welcome { margin: 0; }
    Screen.narrow #controls { width: 27; min-width: 25; }
    Screen.narrow #quick_hint, Screen.narrow #read_only { display: none; }
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
        self._cancel_requested = False
        self._exit_after_step = False
        self._last_outcome: Outcome | None = None
        self._started_at: float | None = None
        self._last_activity_at: float | None = None
        self.advanced_visible = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="screen"):
            yield Static("  ePlus AI Toolkit   |   ePlus.DEV", id="brand")
            yield Static("  Original @gylive  |  Maintained @hoangsvit  |  https://eplus.dev", id="credit")
            with Horizontal(id="details"):
                yield Static("ANDROID DEVICE\nMuMu • Auto-detect", id="device")
                yield Static("GOOGLE ACCOUNT\nNot checked", id="account")
            with Horizontal(id="content"):
                with Vertical(id="controls"):
                    yield Static("NAVIGATION", classes="section")
                    yield Button("Home", id="nav_home")
                    yield Button("Quick Start", id="nav_quick")
                    yield Button("Steps (0-5)  +", id="advanced_toggle")
                    with Vertical(id="advanced"):
                        yield Static("CHOOSE A STEP", id="advanced_label", classes="section")
                        yield Select(
                            [(f"{stage.number}  ·  {stage.label}", stage.number) for stage in STAGES],
                            value=self.initial_step, id="step", allow_blank=False)
                        yield Button("Run selected step", id="run")
                        yield Button("Run sequence from step", id="sequence")
                    yield Button("Help & Guide", id="nav_help")
                    yield Button("Show technical details", id="debug")
                    yield Button("Exit toolkit", id="exit")
                    yield Button("Verified in Google Play → Next", id="next", disabled=True)
                    yield Button("Stop after this step", id="stop", disabled=True)
                    with Vertical(id="workflow"):
                        yield Static("WORKFLOW", classes="section")
                        for stage in STAGES:
                            yield Static(f"○  {stage.number}. {stage.label}",
                                         id=f"stage_{stage.number}", classes="workflow-step")
                with Vertical(id="results"):
                    with Vertical(id="welcome_panel"):
                        yield Static("GET STARTED", id="welcome")
                        yield Static("Check your device and available Google AI offers.", id="quick_hint")
                        yield Button("Check Device & Offers", id="quickstart", variant="primary")
                        yield Static("Read-only. No payment will be made.", id="read_only")
                    with Vertical(id="status_panel"):
                        yield Static("LIVE STATUS", classes="section")
                        yield Static("Ready — no check started", id="state")
                        yield Static("Select Check Device & Offers above to begin.", id="message")
                        yield Static("", id="step_result")
                        yield Static("Elapsed: --", id="elapsed")
                        yield Static("Waiting for your action.", id="activity")
                        yield Button("Completed action on Android", id="manual", disabled=True)
                        yield RichLog(id="debug_log", wrap=True, highlight=False, markup=False)
                        yield Static("Steps 2-5 may request a real Google Play checkout. Verify "
                                     "pricing and renewal terms first.", id="hint")
        yield Footer()

    def on_resize(self, event) -> None:
        self.screen.set_class(event.size.height < 27, "compact")
        self.screen.set_class(event.size.width < 90, "narrow")

    @on(Button.Pressed, "#nav_home")
    def home_pressed(self) -> None:
        if not self.busy:
            self._set_message("Select Check Device & Offers to begin.")

    @on(Button.Pressed, "#nav_quick")
    def quick_pressed(self) -> None:
        self.quickstart_pressed()

    @on(Button.Pressed, "#nav_help")
    def help_pressed(self) -> None:
        self._set_message("Start with a read-only offer check. Steps 2-5 can request "
                          "real payments; verify the account, terms and renewal date.")

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
            "Steps (0-5)  -" if self.advanced_visible else "Steps (0-5)  +"
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

    def _set_workflow(self, step: int, state: str) -> None:
        marker = {"running": "●", "done": "✓", "review": "!"}.get(state, "○")
        self.query_one(f"#stage_{step}", Static).update(
            f"{marker}  {step}. {STAGES[step].label}"
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
        self._cancel_requested = False
        self._exit_after_step = False
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
        self.query_one("#stop", Button).label = "Stop check" if step <= 1 else "Stop after this step"
        self.query_one("#stop", Button).display = True
        self.query_one("#next", Button).display = False
        self.query_one("#step_result", Static).update(f"Step {step} · {STAGES[step].label}")
        self._set_workflow(step, "running")
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
        self.query_one("#stop", Button).display = False
        self._started_at = None
        self.query_one("#activity", Static).update("Step finished. Review the result above.")
        self._set_workflow(step, "done" if outcome.code in ("listed", "environment_ok") else "review")
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
            self.query_one("#next", Button).display = True
        else:
            self.query_one("#next", Button).disabled = True
            self.query_one("#next", Button).display = False
            self.sequence = False
        if outcome.code == "checkout_requested":
            self.notify("Review the actual subscription in Google Play.", severity="warning")
        elif outcome.code not in ("listed", "environment_ok"):
            self.notify("Step stopped; check the result before another attempt.", severity="warning")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ePlus AI Toolkit Textual frontend")
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
