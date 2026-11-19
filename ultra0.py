#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Google AI subscription offer inspection and Android diagnostic CLI.

Usage:
        python ultra0.py --check            # Check Android, ADB, root and Frida
        python ultra0.py accounts.txt       # Legacy batch-account mode
        python ultra0.py --account address@example.com --no-add --no-switch

The legacy accounts.txt format uses four hyphens as a field separator:
    email----password----recovery----totp

Requirements:
        - A rooted Android device/emulator with ADB debugging
        - Google Play Store and Google One with the intended account
        - Python 3 and a compatible Frida client and server

WARNING: non-list mode can open Google Play checkout and tap Subscribe.
Offer metadata does not prove eligibility or subscription activation.
"""
import argparse, base64, hashlib, hmac, json, os, re, select, struct, subprocess, sys, threading, time
from pathlib import Path
import tempfile

# Manual confirmation gate for an unfamiliar Android verification screen.
HUMAN_EVENT = threading.Event()
WAITING = {"on": False, "msg": ""}


def wait_human(msg: str, timeout: int = 600) -> bool:
    """Pause for manual verification or an unfamiliar Android screen."""
    WAITING["on"] = True
    WAITING["msg"] = msg
    print(f"\n⏸  Action required: {msg}")
    print("   Press Enter to continue after completing the step on Android.", flush=True)
    HUMAN_EVENT.clear()
    end = time.time() + timeout
    while time.time() < end:
        if HUMAN_EVENT.is_set():
            break
        try:
            r, _, _ = select.select([sys.stdin], [], [], 0.5)
            if r:
                sys.stdin.readline()
                break
        except Exception:
            time.sleep(0.5)
    WAITING["on"] = False
    print("▶  Continuing", flush=True)
    return True

# ---------- Constants ----------
PKG = "com.google.android.apps.subscriptions.red"   # Google One
VENDING = "com.android.vending"                     # Google Play Store
GMS = "com.google.android.gms"
PRODUCT = "g1.play.20tb"                            # Ultra 5x / 20TB
OFFER = "eft-12month"                               # Historical promotional offer ID
MODULE_REMOTE = "/data/local/tmp/module_521.apk"
FRIDA_REMOTE = "/data/local/tmp/frida-server"
FRIDA_REQUIRED = "16.5.9"
REPORT_DIR = Path("ultra0-report")

ADB_CANDIDATES = [
    os.environ.get("ADB_PATH", ""),
    # Windows / MuMu
    r"C:\Program Files\Netease\MuMuPlayer-12.0\shell\adb.exe",
    r"C:\Program Files\Netease\MuMuPlayerGlobal-12.0\shell\adb.exe",
    r"C:\Program Files\Netease\MuMu\emulator\nemu\vmonitor\bin\adb_server.exe",
    r"C:\Program Files\Netease\MuMu\nx_main\adb.exe",
    r"C:\Program Files (x86)\Netease\MuMuPlayer-12.0\shell\adb.exe",
    "adb.exe", "adb",
    # macOS / Linux
    os.path.expanduser("~/Library/Android/sdk/platform-tools/adb"),
    "/opt/homebrew/bin/adb", "/usr/local/bin/adb", "/usr/bin/adb",
]


# ---------- ADB helpers ----------
def find_adb() -> str:
    for c in ADB_CANDIDATES:
        if not c:
            continue
        if c in ("adb", "adb.exe") or Path(c).exists():
            try:
                subprocess.run([c, "version"], capture_output=True, timeout=5)
                return c
            except Exception:
                continue
    sys.exit("❌ ADB not found. Install Android SDK platform-tools and add adb to PATH.")


ADB = None
SERIAL = None


def sh(*args, timeout=60, check=False, binary=False):
    cmd = [ADB] + (["-s", SERIAL] if SERIAL else []) + list(args)
    p = subprocess.run(cmd, capture_output=True, timeout=timeout)
    if check and p.returncode != 0:
        raise RuntimeError(p.stderr.decode("utf-8", "ignore")[:300])
    return p.stdout if binary else p.stdout.decode("utf-8", "ignore").strip()


def note(msg):
    print(f"   {msg}", flush=True)


def step(msg):
    print(f"\n▶ {msg}", flush=True)


def ok(msg):
    print(f"   ✅ {msg}", flush=True)


def warn(msg):
    print(f"   ⚠️  {msg}", flush=True)


# ---------- Device selection ----------
def pick_device(preferred=None):
    """Select exactly one online Android device; respect an explicit --serial."""
    global SERIAL
    out = sh("devices")
    lines = [l for l in out.splitlines()[1:] if "\tdevice" in l]
    if not lines:
        # When no device is online, probe common emulator ADB ports.
        for port in ("16384", "7555", "16416", "62001", "21503"):
            try:
                sh("connect", f"127.0.0.1:{port}", timeout=10)
            except Exception:
                pass
            out = sh("devices")
            lines = [l for l in out.splitlines()[1:] if "\tdevice" in l]
            if lines:
                note(f"Connected to emulator at 127.0.0.1:{port}")
                break
    if not lines:
        sys.exit("❌ No Android device detected. Start MuMu, enable ADB debugging, or configure ADB_PATH.")
    online = [l.split("\t")[0] for l in lines]
    if preferred and preferred not in online:
        sys.exit(f"❌ ADB device {preferred} is not online. Available: {', '.join(online)}")
    if not preferred and len(online) != 1:
        sys.exit(f"❌ Multiple Android devices: {', '.join(online)}. Choose one with --serial.")
    SERIAL = preferred or online[0]
    ok(f"Connected ADB device: {SERIAL}")


def ensure_root():
    def _id():
        try:
            return sh("shell", "id", timeout=15)
        except Exception:
            return ""

    uid = _id()
    if "uid=0" not in uid:
        # Some emulators support adb root without needing su.
        try:
            sh("root", timeout=20)
            time.sleep(2)
            uid = _id()
            if "uid=0" in uid:
                note("Successfully enabled adb root")
        except Exception:
            pass
    if "uid=0" not in uid:
        try:
            uid = sh("shell", "su -c id", timeout=15)
        except Exception:
            uid = ""
    if "uid=0" not in uid:
        sys.exit("❌ Root is unavailable. Enable root in MuMu settings and restart, or run adb root manually.")


def ensure_frida_client():
    """Pin Frida 16 for the original Java bridge-based script."""
    from importlib.metadata import PackageNotFoundError, version
    try:
        installed = version("frida")
    except PackageNotFoundError:
        installed = "not installed"
    if installed == FRIDA_REQUIRED:
        return
    if os.environ.get("ULTRA0_FRIDA_REPAIR_ATTEMPTED") == "1":
        raise RuntimeError(f"Host Frida is {installed}; expected {FRIDA_REQUIRED}. "
                           f"Manual fix: {sys.executable} -m pip install frida=={FRIDA_REQUIRED}")
    warn(f"Host Frida {installed} is incompatible with the original Java script; installing {FRIDA_REQUIRED}...")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check",
                                 "--no-cache-dir", f"frida=={FRIDA_REQUIRED}"],
                                capture_output=True, text=True, errors="replace", timeout=240)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"Unable to install Frida {FRIDA_REQUIRED}: {exc}") from exc
    if result.returncode:
        msgs = (result.stderr or result.stdout).strip().splitlines()
        raise RuntimeError(f"Frida installation failed: {(msgs[-1] if msgs else 'pip failed')[:240]}")
    note("Frida Python updated; restarting script with the same arguments...")
    os.environ["ULTRA0_FRIDA_REPAIR_ATTEMPTED"] = "1"
    os.environ["ULTRA0_FRIDA_RESTART_SERVER"] = "1"
    os.execv(sys.executable, [sys.executable, *sys.argv])


def ensure_frida_server():
    """Check running Frida version; replace 17.x with the matching 16.5.9 build."""
    ensure_frida_client()
    running = sh("shell", "pidof frida-server || true").strip()
    try:
        deployed_version = sh("shell", f"{FRIDA_REMOTE} --version 2>/dev/null", timeout=12).strip()
    except subprocess.TimeoutExpired:
        deployed_version = ""
    must_restart = os.environ.pop("ULTRA0_FRIDA_RESTART_SERVER", "") == "1"
    if running and deployed_version == FRIDA_REQUIRED and not must_restart:
        ok(f"frida-server {FRIDA_REQUIRED} is running")
        return
    if running:
        warn(f"Restarting frida-server (device version: {deployed_version or 'unknown'})")
        for pid in running.split():
            if pid.isdigit():
                sh("shell", f"kill {pid}")
        time.sleep(1)
        remaining = sh("shell", "pidof frida-server || true").strip()
        if remaining:
            for pid in remaining.split():
                if pid.isdigit():
                    sh("shell", f"su -c 'kill {pid}'")
            time.sleep(1)
        if sh("shell", "pidof frida-server || true").strip():
            raise RuntimeError("Cannot stop old Frida server; restart MuMu and retry")
    if deployed_version != FRIDA_REQUIRED:
        abi = sh("shell", "getprop ro.product.cpu.abi").strip()
        arch = {"arm64-v8a": "arm64", "armeabi-v7a": "arm", "armeabi": "arm",
                "x86_64": "x86_64", "x86": "x86"}.get(abi)
        if not arch:
            raise RuntimeError(f"Unsupported device ABI: {abi}")
        import urllib.request, lzma
        url = (f"https://github.com/frida/frida/releases/download/{FRIDA_REQUIRED}/"
               f"frida-server-{FRIDA_REQUIRED}-android-{arch}.xz")
        archive = Path(tempfile.gettempdir()) / f"frida-server-{FRIDA_REQUIRED}-{arch}.xz"
        extracted = Path(tempfile.gettempdir()) / f"frida-server-{FRIDA_REQUIRED}-{arch}"
        note(f"Downloading official matching Frida server: {url}")
        with urllib.request.urlopen(url, timeout=120) as response, open(archive, "wb") as output:
            output.write(response.read())
        with lzma.open(archive, "rb") as source, open(extracted, "wb") as output:
            output.write(source.read())
        sh("push", str(extracted), FRIDA_REMOTE, timeout=180, check=True)
        sh("shell", f"chmod 755 {FRIDA_REMOTE}", check=True)
    if "uid=0" in sh("shell", "id"):
        sh("shell", f"nohup {FRIDA_REMOTE} -D >/dev/null 2>&1 &", timeout=15)
    else:
        sh("shell", f"su -c 'nohup {FRIDA_REMOTE} -D >/dev/null 2>&1 &'", timeout=15)
    for _ in range(20):
        time.sleep(0.5)
        if sh("shell", "pidof frida-server || true").strip():
            ok(f"frida-server {FRIDA_REQUIRED} started")
            return
    raise RuntimeError(f"frida-server {FRIDA_REQUIRED} could not start")


def read_purchase_token(sku_short: str) -> str:
    """Read a purchase token from Google Play library.db for the legacy subscription update flow."""
    import tempfile, sqlite3, json as _json
    remote = "/data/local/tmp/lib_read.db"
    try:
        sh("shell", f"cp /data/data/{VENDING}/databases/library.db {remote} 2>/dev/null; chmod 666 {remote}", timeout=30)
    except Exception:
        pass
    tmp = Path(tempfile.gettempdir()) / "lib_read.db"
    try:
        if tmp.exists():
            tmp.unlink()
        sh("pull", remote, str(tmp), timeout=60)
    except Exception as e:
        warn(f"Failed to retrieve library.db: {e}")
        return ""
    if not tmp.exists():
        return ""
    tok = ""
    try:
        con = sqlite3.connect(str(tmp))
        cur = con.cursor()
        rows = cur.execute(
            "select account, subs_valid_until_time, inapp_purchase_data "
            "from ownership where doc_id like ?",
            (f"%{sku_short}%",),
        ).fetchall()
        now_ms = int(time.time() * 1000)
        picked = None
        for account, valid, data in rows:
            if not data:
                continue
            try:
                j = _json.loads(data)
            except Exception:
                continue
            tk = j.get("purchaseToken")
            if not tk:
                continue
            try:
                alive = int(valid) > now_ms
            except Exception:
                alive = False
            # Prefer unexpired records; if several are active, select the latest expiry.
            if picked is None or (alive and not picked[2]) or (alive == picked[2] and int(valid or 0) > picked[3]):
                picked = (tk, account, alive, int(valid or 0))
        if picked:
            tok = picked[0]
            note(f"Purchase token account: {picked[1]} ({'active' if picked[2] else 'expired'})")
        con.close()
    except Exception as e:
        warn(f"Failed to read library.db: {e}")
    finally:
        try:
            tmp.unlink()
        except Exception:
            pass
    return tok


def ensure_vending():
    """Google Play Store must be running for BillingClient queries to complete."""
    if sh("shell", f"pidof {VENDING}"):
        ok("Google Play Store process is running")
        return
    warn("Google Play Store is not running; attempting to start it...")
    sh("shell", f"monkey -p {VENDING} -c android.intent.category.LAUNCHER 1", timeout=30)
    for _ in range(20):
        time.sleep(1)
        if sh("shell", f"pidof {VENDING}"):
            ok("Google Play Store started")
            time.sleep(2)
            return
    warn("Google Play Store did not start. Open it manually or restart the emulator.")


def ensure_module_apk():
    if sh("shell", f"ls {MODULE_REMOTE} 2>/dev/null"):
        ok("Billing module is already installed")
        return
    note("Pushing billing module to Android (one-time setup)...")
    tmp = Path(tempfile.gettempdir()) / "module_521.apk"
    tmp.write_bytes(base64.b64decode(MODULE_B64))
    sh("push", str(tmp), MODULE_REMOTE, timeout=120)
    ok("Billing module installed")


def ensure_network():
    proxy = sh("shell", "settings get global http_proxy")
    if proxy and proxy != "null" and proxy != ":0":
        sh("shell", "settings put global http_proxy :0")
        warn(f"Cleared Android proxy (previous value: {proxy}) to restore network access")
    # Stop common VPN apps that may intercept Google Play network traffic.
    for p in ("com.github.metacubex.clash.meta", "com.github.kr328.clash"):
        if sh("shell", f"pm list packages | grep -q {p} && echo yes"):
            sh("shell", f"am force-stop {p}")
            warn(f"Temporarily stopped {p}, which may intercept Google Play traffic")


# ---------- UI ----------
def ui_xml() -> str:
    sh("shell", "uiautomator dump /sdcard/ui.xml")
    return sh("shell", "cat /sdcard/ui.xml")


def nodes(xml: str):
    for m in re.finditer(r"<node[^>]*>", xml):
        s = m.group(0)
        t = re.search(r'text="([^"]*)"', s)
        d = re.search(r'content-desc="([^"]*)"', s)
        b = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', s)
        c = re.search(r'class="([^"]*)"', s)
        if not b:
            continue
        yield {
            "text": (t.group(1) if t else "") or "",
            "desc": (d.group(1) if d else "") or "",
            "cls": (c.group(1) if c else "") or "",
            "x": (int(b.group(1)) + int(b.group(3))) // 2,
            "y": (int(b.group(2)) + int(b.group(4))) // 2,
        }


def tap(x, y):
    sh("shell", f"input tap {x} {y}")


def tap_text(*needles, exact=False) -> bool:
    for n in nodes(ui_xml()):
        label = n["text"] or n["desc"]
        if not label:
            continue
        hit = (label == needles[0]) if exact and needles else any(k in label for k in needles)
        if hit and (n["x"] or n["y"]):
            tap(n["x"], n["y"])
            return True
    return False


def type_text(s: str):
    sh("shell", f"input text '{s.replace(' ', '%s')}'")


def find_edit():
    for n in nodes(ui_xml()):
        if "EditText" in n["cls"]:
            return n["x"], n["y"]
    return None


# ---------- TOTP ----------
def totp(secret: str, digits=6, period=30) -> str:
    if not secret:
        return ""
    s = re.sub(r"[^A-Za-z2-7]", "", secret).upper()
    s += "=" * ((8 - len(s) % 8) % 8)
    key = base64.b32decode(s)
    ctr = int(time.time()) // period
    mac = hmac.new(key, struct.pack(">Q", ctr), hashlib.sha1).digest()
    off = mac[-1] & 0x0F
    code = (struct.unpack(">I", mac[off:off + 4])[0] & 0x7FFFFFFF) % (10 ** digits)
    return str(code).zfill(digits)


# ---------- Account management ----------
def accounts_on_device() -> list:
    out = sh("shell", "dumpsys account | grep 'type=com.google'")
    return out.splitlines()


def add_account(email, password, totp_secret="") -> bool:
    """Add a Google account on Android, pausing for manual verification when needed."""
    step(f"Adding account to Android: {email}")
    before = len(accounts_on_device())
    sh("shell", "am start -a android.settings.ADD_ACCOUNT_SETTINGS")
    time.sleep(3)
    tap_text("Google", exact=True) or tap_text("Google")
    time.sleep(5)

    pos = find_edit()
    if pos:
        for _ in range(3):                      # Verify the typed email to catch missing characters.
            tap(*pos); time.sleep(0.8)
            sh("shell", "input keyevent 123")   # Move cursor to end.
            for _ in range(60):
                sh("shell", "input keyevent 67")  # Backspace to clear the field.
            type_text(email); time.sleep(1)
            cur = " ".join(n["text"] for n in nodes(ui_xml()) if "@" in n["text"])
            if email.lower() in cur.lower():
                break
            warn(f"Email input was incomplete; retrying (current: {cur[:40]})")
        else:
            warn("Could not enter the complete email after several attempts")
        tap_text("下一步", "Next"); time.sleep(6)

    if find_edit():
        tap(*find_edit()); time.sleep(1)
        type_text(password); time.sleep(1)
        tap_text("下一步", "Next"); time.sleep(7)

    # Advance through recognized screens; ask the user to handle unknown screens.
    unknown_rounds = 0
    for _ in range(90):
        if len(accounts_on_device()) > before:
            ok("Google account added to Android")
            return True
        xml = ui_xml()
        text = " ".join(n["text"] for n in nodes(xml) if n["text"])

        if "此账号已在您的设备上" in text or "already on your device" in text.lower():
            ok("This Google account is already on the device")
            return True
        if "找不到此账号" in text or "Couldn't find your Google Account" in text:
            warn("Google could not find this account; check the email address")
            return False
        if "密码不正确" in text or "Wrong password" in text:
            warn("Google account password was rejected")
            return False

        if ("两步验证" in text or "2-Step" in text or "输入验证码" in text):
            if totp_secret and find_edit():
                code = totp(totp_secret)
                note(f"Two-factor verification code: {code}")
                tap(*find_edit()); type_text(code); time.sleep(1)
                tap_text("下一步", "Next"); time.sleep(8)
                continue
            wait_human("Two-step verification required; complete the check on Android.", 300)
            continue

        if tap_text("以后再说", "Not now"):
            time.sleep(3); continue
        if tap_text("我同意", "I agree"):
            time.sleep(5); continue
        if tap_text("取消", "Skip", "跳过"):
            time.sleep(2); continue

        if any(k in text for k in ("证明您不是自动程序", "验证身份", "请输入电话号码", "无法验证", "确认是您本人")):
            wait_human("Complete the CAPTCHA or identity verification on Android.", 300)
            continue

        unknown_rounds += 1
        if unknown_rounds >= 8:
            wait_human("Unrecognized Android screen; finish account setup manually.", 300)
            unknown_rounds = 0
        time.sleep(2)

    if len(accounts_on_device()) > before:
        ok("Google account added to Android")
        return True
    warn("Timed out adding the Google account")
    return False


def add_card(card: dict) -> bool:
    """Add a payment card through the original Google Pay UI workflow."""
    if not card:
        return True
    step(f"Adding a payment method ending in {card['number'][-4:]}")
    sh("shell", "am start -a android.intent.action.VIEW "
                "-d 'https://pay.google.com/gp/w/u/0/home/paymentmethods'")
    time.sleep(10)
    if not tap_text("Add a payment method", "添加付款方式", "添加信用卡", "Add card"):
        warn("Could not find the add-card entry; enter the payment method manually")
        return False
    time.sleep(9)
    # Field order: card number, month, year, CVC, name, street, and city.
    edits = [n for n in nodes(ui_xml()) if "EditText" in n["cls"]]
    mm = re.sub(r"\D", "", card["exp"])[:2] or "01"
    yy = re.sub(r"\D", "", card["exp"])[2:][-2:] or "30"
    seq = [card["number"], mm, yy, card["cvc"], card["holder"] or "CARD HOLDER",
           "123 Main St", "Portland"]
    for i, val in enumerate(seq):
        edits = [n for n in nodes(ui_xml()) if "EditText" in n["cls"]]
        if i >= len(edits):
            break
        tap(edits[i]["x"], edits[i]["y"]); time.sleep(0.6)
        type_text(val); time.sleep(0.5)
    if not tap_text("Save", "保存"):
        wait_human("Tap Save in Google Pay manually, then continue.", 240)
    else:
        time.sleep(8)
    ok("Payment method form submitted")
    return True


def current_play_account() -> str:
    """Read the visible account from Play Store; unknown is not an account mismatch."""
    xml = ui_xml()
    if f'package="{VENDING}"' not in xml:
        note("Opening Play Store to verify the account (Google One may be foreground)...")
        sh("shell", f"am start -n {VENDING}/com.google.android.finsky.activities.MainActivity", timeout=25)
        time.sleep(3)
        xml = ui_xml()
    if f'package="{VENDING}"' not in xml:
        warn("Cannot inspect Play Store UI. Open Play Store, tap the profile icon, and retry.")
        return ""

    opened_profile = False
    for n in nodes(xml):
        if ("账号和设置" in n["desc"] or "Account and settings" in n["desc"]
                or "Tài khoản và chế độ cài đặt" in n["desc"]):
            tap(n["x"], n["y"])
            time.sleep(3)
            opened_profile = True
            break
    best = ""
    for n in nodes(ui_xml()):
        m = re.search(r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+)", n["desc"] + " " + n["text"])
        if m:
            best = m.group(1).lower()
            break
    if opened_profile:
        sh("shell", "input keyevent 4")
    if not best:
        warn("Play account is not visible to UI automation; check the Play Store profile manually.")
    return best


def switch_play(email) -> bool:
    """Switch Play Store account, but fail closed when the active account cannot be verified."""
    step(f"Switching to Play Store account: {email}")
    want = email.lower()
    sh("shell", f"am force-stop {VENDING}")
    sh("shell", f"am force-stop {PKG}")
    sh("shell", f"am start -n {VENDING}/com.google.android.finsky.activities.MainActivity "
                f"--es authAccount {email}")
    time.sleep(9)
    if current_play_account() == want:
        ok("Google Play account verified"); return True
    for n in nodes(ui_xml()):
        if "账号和设置" in n["desc"] or "Account and settings" in n["desc"]:
            tap(n["x"], n["y"]); time.sleep(3); break
    for n in nodes(ui_xml()):
        if "展开账号列表" in n["desc"]:
            tap(n["x"], n["y"]); time.sleep(3); break
    for n in nodes(ui_xml()):
        if want in (n["text"] + " " + n["desc"]).lower():
            tap(n["x"], n["y"]); time.sleep(6); break
    sh("shell", "input keyevent 4")
    got = current_play_account()
    if got == want:
        ok("Google Play account verified"); return True
    warn(f"Google Play account did not switch (current: {got or 'unknown'}). Aborting to avoid the wrong account.")
    return False


# ---------- Frida ----------
def launch_app() -> int:
    """Start Google One and wait for a real PID; report launch failures clearly."""
    if not sh("shell", f"pm path {PKG}", timeout=15).strip():
        warn(f"Google One is not installed or enabled ({PKG}). Install/open it from Play Store.")
        return 0
    sh("shell", f"am force-stop {PKG}")
    try:
        launch_output = sh("shell", f"monkey -p {PKG} -c android.intent.category.LAUNCHER 1", timeout=30)
    except subprocess.TimeoutExpired:
        warn("Google One launch (monkey) timed out; inspect the emulator screen.")
        launch_output = ""
    if "No activities found" in launch_output:
        warn("Google One has no launchable activity on this Android instance.")
        return 0
    for seconds in (7, 3, 3, 3):
        time.sleep(seconds)
        pid = sh("shell", f"pidof {PKG}").strip()
        if pid.isdigit():
            return int(pid)
    warn("Google One stopped or did not launch after 16 seconds. Open it manually in MuMu.")
    warn(f"Diagnostics: adb shell pm path {PKG} ; adb shell monkey -p {PKG} -c android.intent.category.LAUNCHER 1")
    return 0


def build_js(plan: str = "auto", list_only: bool = False, stack: bool = False, old_token: str = "", stack_mode=None, activity_method="auto") -> str:
    """Build the product query for the requested Google Play plan."""
    if activity_method not in ("auto", "choose", "thread"):
        raise ValueError(f"Unsupported activity method: {activity_method}")
    js = FRIDA_JS.replace('var ACTIVITY_METHOD="auto";',
                          f'var ACTIVITY_METHOD="{activity_method}";', 1)
    if list_only:
        js = js.replace('var PREFER="";', 'var PREFER=""; var LIST_ONLY=true;', 1)
    if stack:
        js = js.replace('var PREFER="";', 'var PREFER=""; var STACK=true;', 1)
    if old_token:
        js = js.replace('var PREFER="";', 'var PREFER=""; var OLD_TOKEN="%s";' % old_token, 1)
    if stack_mode is not None:
        js = js.replace('var PREFER="";', 'var PREFER=""; var STACK_MODE=%d;' % stack_mode, 1)
    if plan == "20x":
        js = js.replace('var PRODUCTS=["g1.play.20tb","g1.play.ai.pro","g1.30tb"];',
                        'var PRODUCTS=["g1.play.ai.pro","g1.ai.pro","g1.30tb"];')
    elif plan == "5x":
        js = js.replace('var PRODUCTS=["g1.play.20tb","g1.play.ai.pro","g1.30tb"];',
                        'var PRODUCTS=["g1.play.20tb"];')
    elif plan.startswith("pro"):
        # Google AI Pro 5TB（g1.2tb.ai.subs_variant）：12months-eft / 6months-eft / 6months-eft-2 / 6months-eft-ss-2026
        prefer = {"pro12": "12months-eft", "pro6": "6months-eft",
                  "pro6b": "6months-eft-2", "pro6c": "6months-eft-ss-2026"}.get(plan, "12months-eft")
        js = js.replace('var PRODUCTS=["g1.play.20tb","g1.play.ai.pro","g1.30tb"];',
                        'var PRODUCTS=["g1.2tb.ai.subs_variant"];')
        js = js.replace('var PREFER="";', 'var PREFER="%s";' % prefer, 1)
    return js


def run_trial(pid: int, wait=90, plan="auto", list_only=False, stack=False, old_token="", stack_mode=None, activity_method="auto") -> dict:
    import frida
    step("Injecting billing module to inspect introductory offers")
    dev = frida.get_usb_device(timeout=10)
    sess = dev.attach(pid)
    res = {"offers": [], "launched": None, "purchase": None, "activity": None, "errors": []}

    def on_msg(m, _):
        if m.get("type") == "error":
            detail = str(m.get("description") or m.get("stack") or "Unknown JavaScript error")
            res["errors"].append({"ev": "frida_script_error", "message": detail[:400]})
            warn(f"Frida JavaScript error: {detail[:240]}")
            return
        p = m.get("payload") or {}
        if not isinstance(p, dict):
            return
        ev = p.get("ev")
        if ev == "offer":
            res["offers"].append(p)
            note(f"offer {p.get('id')} → {p.get('micros')} ({p.get('period','')})")
            # Offer tokens are private checkout inputs; do not print them in terminal.
        elif ev == "activity_selected":
            res["activity"] = {"method": p.get("method"), "class": p.get("name")}
            note(f"Activity found via {p.get('method')}: {p.get('name')}")
        elif ev == "launched":
            res["launched"] = p
            ok(f"Google Play billing flow response: {p}")
        elif ev == "purchase_cb":
            res["purchase"] = p
        elif ev and ("err" in ev or ev.startswith("no_")):
            res["errors"].append(p)

    sc = sess.create_script(build_js(plan, list_only, stack, old_token, stack_mode, activity_method))
    sc.on("message", on_msg)
    sc.load()
    time.sleep(wait)
    return res


def diagnose_launch_failure(fr: dict) -> tuple:
    """Explain why billing UI was not opened, without retrying purchases."""
    events = fr.get("errors") or []
    ev_names = {e.get("ev") for e in events if isinstance(e, dict)}
    if "choose_err" in ev_names and ("activity_thread_err" in ev_names or "no_activity" in ev_names):
        return ("activity_lookup_failed",
                "Both Java.choose and ActivityThread failed to locate a usable Activity. "
                "Check the recorded ART errors and the Android version; no checkout was opened.")
    if "choose_err" in ev_names:
        return ("activity_lookup_failed",
                "Java.choose failed; rerun with --activity-method thread to test the fallback.")
    if "activity_thread_err" in ev_names:
        return ("activity_lookup_failed",
                "ActivityThread lookup failed; try --activity-method choose on a compatible device.")
    if "no_activity" in ev_names:
        return ("no_activity",
                "Google One had no usable Android Activity; reopen the app in MuMu.")
    for event in events:
        if isinstance(event, dict) and event.get("ev") in (
                "launch_err", "launch_outer_err", "mode_err", "frida_script_error"):
            message = str(event.get("m") or event.get("message") or event["ev"])[:240]
            return ("billing_launch_error", message)
    result = fr.get("launched")
    if isinstance(result, dict):
        code = result.get("code")
        message = str(result.get("msg") or "")[:180]
        return ("billing_flow_error",
                f"BillingClient launchBillingFlow returned code={code}; message={message}.")
    return ("launch_failed",
            "No successful launchBillingFlow response was observed. "
            "Inspect the report's errors field; do not infer subscription success.")


def handle_verify(password="") -> bool:
    """Handle optional Google Play identity verification and Play Points prompts."""
    changed = False
    for _ in range(12):
        blob = " ".join(n["text"] for n in nodes(ui_xml()) if n["text"])
        if "以后再说" in blob or "Play 积分" in blob:
            tap_text("以后再说", "Not now"); time.sleep(2); changed = True; continue
        if ("验证" in blob or "Verify" in blob) and password:
            es = [n for n in nodes(ui_xml()) if "EditText" in n["cls"]]
            if es:
                tap(es[0]["x"], es[0]["y"]); time.sleep(0.8)
                slow_type(password, 0.1); time.sleep(0.8)
                tap_text("验证", "Verify"); time.sleep(6); changed = True; continue
        break
    return changed


def confirm_zero(wait=40, password="") -> dict:
    step("检查收银台金额（只在 0 元时确认）")
    out = {"price": None, "confirmed": False, "ineligible": False, "text": ""}
    for _ in range(wait // 2):
        xml = ui_xml()
        text = " ".join(n["text"] for n in nodes(xml) if n["text"])
        if "不符合免费试用条件" in text or "not eligible" in text.lower():
            warn("Play 提示：该账号不符合免费试用条件")
            if tap_text("知道了", "OK", "Got it"):
                time.sleep(2)
            out["ineligible"] = True
            return out
        if ("订阅" in text or "Subscribe" in text) and ("Ultra" in text or "AI" in text):
            out["text"] = text[:300]
            m = re.search(r"(US\$|HK\$|NT\$|\$|€|£)\s?([\d.,]+)", text)
            if m:
                out["price"] = m.group(0)
                try:
                    if float(m.group(2).replace(",", "")) == 0:
                        tap_text("订阅", "Subscribe")
                        out["confirmed"] = True
                        ok("已确认 0 元订阅")
                        return out
                except Exception:
                    pass
                warn(f"当前金额 {m.group(0)}，不是 0 元，不点确认")
                return out
            if ("不符合免费试用条件" in text) or ("not eligible" in text.lower()):
                out["ineligible"] = True
                warn("Play：该账号不符合免费试用条件，不点确认")
                tap_text("关闭", "取消", "Close"); return out
            if (re.search(r"(US\$|HK\$|NT\$|\$)\s?0(\.00)?\b", text)
                    or "US$0/月" in text or "US$0.00" in text
                    or re.search(r"免费试用\s*\d+\s*(个月|年|mo|month)", text)):
                tap_text("订阅", "Subscribe")
                out["confirmed"] = True
                ok("已确认免费试用")
                return out
        time.sleep(2)
    warn("没有检测到收银台（可能这个号已经订阅过）")
    return out


def verify() -> str:
    step("核对订阅状态")
    sh("shell", f"am start -a android.intent.action.VIEW "
                f"-d 'https://play.google.com/store/account/subscriptions'")
    time.sleep(9)
    text = " | ".join(n["text"] for n in nodes(ui_xml()) if n["text"])
    if "Ultra" in text:
        ok("订阅页已显示 Ultra")
    return text[:500]


# ---------- 单号流程 ----------
def process(email, password="", totp_secret="", add=True, card=None, plan="auto", no_switch=False, list_only=False, stack=False, old_token="", stack_mode=None, activity_method="auto") -> dict:
    print("\n" + "=" * 56)
    print(f"  处理账号：{email}")
    print("=" * 56)
    rec = {"email": email, "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "status": "unknown"}
    if add:
        try:
            if not add_account(email, password, totp_secret):
                rec["status"] = "add_account_failed"
                return rec
        except Exception as e:
            warn(f"加号失败：{e}")
            rec["status"] = "add_account_error"
            return rec
    if card:
        try:
            add_card(card)
        except Exception as e:
            warn(f"绑卡失败：{e}")
    if globals().get("SKIP_ACCOUNT_CHECK"):
        ok("已跳过 Play 账号校验（--force）")
    elif list_only:
        cur = current_play_account()
        ok(f"列表模式：使用设备当前账号 {cur or '未知'}（不校验、不下单）")
    elif no_switch:
        cur = current_play_account()
        if not cur:
            warn("Play Store account could not be verified; aborting without checkout.")
            rec["status"] = "account_unverified"
            rec["error"] = "Play Store profile email was not readable; check the foreground Play Store UI"
            return rec
        if cur != email.lower():
            warn(f"当前 Play 账号是 {cur}，不是 {email}，中止")
            rec["status"] = "wrong_account"
            return rec
        ok("Play 账号已确认（手动切换模式）")
    elif not switch_play(email):
        rec["status"] = "play_account_switch_failed"
        return rec
    if stack and not old_token:
        note("正在读取当前订阅的 purchaseToken…")
        old_token = read_purchase_token("subs_variant")
        if old_token:
            ok(f"已读到 purchaseToken（{old_token[:16]}…），将用订阅升级模式叠加")
        else:
            warn("没读到 purchaseToken，将退回 queryPurchases 方式（可能拿不到）")

    pid = launch_app()
    if not pid:
        rec["status"] = "app_not_started"
        return rec
    fr = run_trial(pid, plan=plan, list_only=list_only, stack=stack, old_token=old_token,
                   stack_mode=stack_mode, activity_method=activity_method)
    rec.update(fr)
    if list_only:
        rec["status"] = "listed"
        return rec
    if fr["launched"] and fr["launched"].get("code") == 0:
        rec["sheet"] = confirm_zero(password=password)
        rec["subscription_page"] = verify()
        rec["status"] = "subscribed" if "Ultra" in rec["subscription_page"] else "launched"
    else:
        rec["status"], rec["error"] = diagnose_launch_failure(fr)
        warn(f"Checkout not opened: {rec['status']}: {rec['error']}")
    return rec


# ---------- 入口 ----------
def do_check(serial=None):
    global ADB
    ADB = find_adb()
    ok(f"adb：{ADB}")
    pick_device(serial)
    ensure_root()
    ensure_network()
    ensure_frida_server()
    ensure_module_apk()
    ensure_vending()
    try:
        import frida
        ok(f"frida：{frida.__version__}")
    except Exception:
        warn("电脑没装 frida，请执行：pip3 install frida")
    ok("环境自检通过，可以开始跑号了")
    return 0


def parse_accounts(path: Path):
    """每行：邮箱----密码----辅助邮箱----2FA----卡号----有效期----CVC----持卡人----邮编"""
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("----")]
        while len(parts) < 9:
            parts.append("")
        rows.append(parts[:9])
    return rows


def parse_card(parts) -> dict | None:
    """从账号行里取卡信息（第 5~9 项）。"""
    if len(parts) < 5 or not parts[4]:
        return None
    return {
        "number": re.sub(r"\s+", "", parts[4]),
        "exp": parts[5] or "",
        "cvc": parts[6] or "",
        "holder": parts[7] or "",
        "zip": parts[8] or "97201",
    }


def main():
    global ADB, SERIAL
    ap = argparse.ArgumentParser(description="Google AI Ultra 0 元开通一键脚本")
    ap.add_argument("accounts", nargs="?", help="账号文件（每行 email----password----recovery----totp）")
    ap.add_argument("--account", help="单号：email:password:totp")
    ap.add_argument("--check", action="store_true", help="只做环境自检")
    ap.add_argument("--list", action="store_true", help="只列出 offer 和 token，不拉起收银台（零风险）")
    ap.add_argument("--force", action="store_true", help="跳过 Play 账号校验（读不到账号时用）")
    ap.add_argument("--mode", type=int, default=None,
                    help="替换模式：1=TIME_PRORATION 2=CHARGE_PRORATED_PRICE 3=WITHOUT_PRORATION 4=DEFERRED 5=CHARGE_FULL_PRICE")
    ap.add_argument("--old-token", default="",
                    help="当前订阅的 purchaseToken（配合 --stack，直接用它做升级，跳过 queryPurchases）")
    ap.add_argument("--stack", action="store_true",
                    help="订阅升级叠加：用旧 purchaseToken + CHARGE_FULL_PRICE 拉起结算，剩余试用期会折算顺延")
    ap.add_argument("--serial", default=None, help="ADB serial; required if multiple devices are online")
    ap.add_argument("--activity-method", choices=["auto", "choose", "thread"], default="auto",
                    help="Android Activity lookup: auto=Java.choose then ActivityThread fallback")
    ap.add_argument("--no-add", action="store_true", help="跳过自动加号（账号已在手机上）")
    ap.add_argument("--no-switch", action="store_true",
                    help="不自动切号，只校验当前 Play 账号是否为目标号")
    ap.add_argument("--plan", default="auto", choices=["auto", "5x", "20x", "pro12", "pro6", "pro6b", "pro6c"],
                    help="auto=两档都查挑最长；5x=Ultra 20TB；20x=Ultra 30TB")
    a = ap.parse_args()

    ADB = find_adb()
    globals()["SKIP_ACCOUNT_CHECK"] = bool(a.force)
    if a.check:
        return do_check(serial=a.serial)

    pick_device(preferred=a.serial)
    ensure_root()
    ensure_network()
    ensure_frida_server()
    ensure_module_apk()
    ensure_vending()   # Play 商店必须在跑，否则计费查询永远不回调

    REPORT_DIR.mkdir(exist_ok=True)
    rows = []
    if a.list and not a.account and not a.accounts:
        a.account = "current@device"
    if a.account:
        parts = a.account.split(":")
        rows = [[parts[0], parts[1] if len(parts) > 1 else "", "", parts[2] if len(parts) > 2 else ""]]
    elif a.accounts:
        rows = parse_accounts(Path(a.accounts))
    else:
        ap.print_help()
        return 1

    print(f"\n共 {len(rows)} 个账号，开始执行\n")
    results = []
    for i, row in enumerate(rows, 1):
        email, pw, _rec, sec = row[0], row[1], row[2], row[3]
        card = parse_card(row)
        print(f"\n──── 进度 {i}/{len(rows)} ────")
        try:
            rec = process(email, pw, sec, add=(not a.no_add and not a.list), card=card, plan=a.plan,
                          no_switch=a.no_switch, list_only=a.list, stack=a.stack, old_token=a.old_token,
                          stack_mode=a.mode, activity_method=a.activity_method)
        except Exception as e:
            warn(f"{type(e).__name__}: {str(e)[:320]}")
            rec = {"email": email, "status": "exception", "error": str(e)[:320],
                   "exception_type": type(e).__name__}
        results.append(rec)
        (REPORT_DIR / f"{email.split('@')[0]}.json").write_text(
            json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"   结果：{rec.get('status')}")

    print("\n" + "=" * 56)
    print("  汇总")
    print("=" * 56)
    for r in results:
        print(f"  {r['email']:<42} {r.get('status')}")
    print(f"\n明细已保存到 {REPORT_DIR.resolve()}")
    return 0


entry = main


# The original BillingClient hook and embedded DEX archive are maintained as assets.
# Paths are relative to this file, not the process working directory.
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
FRIDA_JS = (ASSETS_DIR / "frida" / "billing.js").read_text(encoding="utf-8")
MODULE_B64 = (ASSETS_DIR / "modules" / "module_521.b64").read_text(encoding="ascii").strip()

if __name__ == "__main__":
    sys.exit(entry())





