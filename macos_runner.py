#!/usr/bin/env python3
"""Mac diagnostic bridge: only Steps 0 and 1; never launch billing."""
from __future__ import annotations

import argparse
from importlib import metadata
import os
from pathlib import Path
import shutil
import subprocess
import sys

from device_selector import auto_select_device, online_serials

ROOT = Path(__file__).resolve().parent
FRIDA_REQUIRED = "16.5.9"


def readonly_command(step: int, serial: str, python: str = sys.executable) -> list[str]:
    if type(step) is not int or step not in (0, 1):
        raise ValueError("macOS supports diagnostic Steps 0 and 1 only")
    if not serial or serial.startswith("-"):
        raise ValueError("A verified ADB serial is required")
    base = [python, str(ROOT / "ultra0.py")]
    if step == 0:
        return base + ["--check", "--serial", serial]
    return base + ["--list", "--no-add", "--no-switch", "--plan", "pro12",
                   "--account", "current@device", "--serial", serial]


def preflight() -> tuple[str, str]:
    adb = os.environ.get("ADB_PATH") or shutil.which("adb")
    if not adb:
        raise RuntimeError("ADB is not installed. Install Android SDK Platform-Tools.")
    try:
        installed = metadata.version("frida")
    except metadata.PackageNotFoundError:
        installed = None
    if installed != FRIDA_REQUIRED:
        raise RuntimeError(
            f"Frida {FRIDA_REQUIRED} is required (found: {installed or 'none'}). "
            "Use run-macos.sh to install it into the isolated .venv."
        )
    online = online_serials(adb)
    if not online:
        raise RuntimeError("No online Android device. Check 'adb devices' and authorization.")
    serial = auto_select_device(adb, serials=online)
    if not serial:
        raise RuntimeError("Multiple different Android devices detected; disconnect extras.")
    return adb, serial


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="macOS Android diagnostic adapter (Steps 0–1 only)")
    parser.add_argument("--step", type=int, required=True, choices=(0, 1))
    args = parser.parse_args(argv)
    try:
        adb, serial = preflight()
        command = readonly_command(args.step, serial)
        env = os.environ.copy()
        env["ADB_PATH"] = adb
        env["PYTHONIOENCODING"] = "utf-8:backslashreplace"
        env["PYTHONUTF8"] = "1"
        print(f"Device {serial}", flush=True)
        print("Checking Android environment (may modify emulator settings)..."
              if args.step == 0 else
              "Checking Google Play offers (no subscription checkout)...", flush=True)
        return subprocess.call(command, cwd=ROOT, env=env)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Diagnostic error: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
