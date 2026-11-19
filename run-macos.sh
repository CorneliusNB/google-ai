#!/bin/sh
# macOS preview: Android diagnostics only, no subscription checkout.
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

usage() {
  printf '%s\n' \
    "ePlus AI Toolkit — macOS diagnostic preview" \
    "Usage: sh run-macos.sh [--check | --list | --help]" \
    "  (no flags)    Textual dashboard (Steps 0–1 only)" \
    "  --check       Android/Frida preflight; may change emulator settings" \
    "  --list        Google Play offers; no checkout" \
    "Steps 2–5 and subscription sequences are disabled."
}

case "${1:-}" in
  --help|-h)
    if [ "$#" -eq 1 ]; then usage; exit 0; fi ;;
  --check|--list|"")
    if [ "$#" -le 1 ]; then :; else usage >&2; exit 2; fi ;;
  *) usage >&2; exit 2 ;;
esac
if [ "$(uname -s)" != "Darwin" ]; then
  printf '%s\n' "macOS only. On Windows run .\run-all.ps1" >&2
  exit 2
fi
if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' "Install Python 3.10+ to run this toolkit." >&2
  exit 2
fi
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
  printf '%s\n' "Python 3.10+ is required." >&2
  exit 2
fi
if ! command -v adb >/dev/null 2>&1; then
  printf '%s\n' "Install Android SDK Platform-Tools, then check 'adb devices'." >&2
  exit 2
fi
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi
PYTHON=.venv/bin/python
if ! "$PYTHON" -c "import importlib.metadata as m; import textual, frida; assert m.version('frida') == '16.5.9'" >/dev/null 2>&1; then
  "$PYTHON" -m pip install --disable-pip-version-check -r requirements-tui.txt 'frida==16.5.9'
fi
export PYTHONIOENCODING=utf-8:backslashreplace
export PYTHONUTF8=1
case "${1:-}" in
  --check) exec "$PYTHON" macos_runner.py --step 0 ;;
  --list)  exec "$PYTHON" macos_runner.py --step 1 ;;
  "")      exec "$PYTHON" tui.py ;;
esac
exit 2
