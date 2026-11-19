# ePlus AI Toolkit

A Windows-focused terminal toolkit for inspecting Google AI Pro offers through an Android emulator, ADB, Frida and Google Play. The Textual dashboard wraps the existing PowerShell/Python engine and preserves the original author's workflow.

<img width="1902" height="912" alt="ePlus AI Toolkit terminal dashboard" src="https://github.com/user-attachments/assets/f16cde7e-022f-43bc-97fe-310012b0a5d3" />

> [!CAUTION]
> **Unofficial project. Potential billing charges.** Steps **2–5** can open a real Google Play checkout and may automatically tap **Subscribe**. An offer appearing in a list, a displayed first-phase price of zero, or a `checkout_requested` report does **not** establish eligibility, an active subscription, a free subscription, or a changed renewal date. Verify the exact account, today's charge, future pricing and renewal date directly in Google Play before any checkout.

## Install and prepare

### Requirements

- **Windows** with PowerShell **5.1+** and Python **3.10+**.
- **MuMuPlayer installed separately**, started with an Android instance that permits root and ADB access.
- **Google Play Store** and **Google One** installed and signed into the intended Google account inside Android.
- A connection to Android through ADB. The toolkit can locate or download **Android SDK Platform-Tools** when ADB is missing; it does **not** install the Android emulator.
- A compatible **Frida 16.5.9** host/device environment. The setup helper can prepare Frida, but compatibility depends on the emulator and Android version.

### Step 1 — Install MuMuPlayer

**MuMuPlayer is neither included in this repository nor automatically downloaded by the toolkit.**

Download it from the **[official MuMuPlayer website (NetEase)](https://www.mumuplayer.com/download/)**, choose the Windows edition, and install it yourself. Avoid third-party download mirrors.

Start MuMuPlayer, enable root and ADB debugging for the Android instance, and ensure Google Play Store and Google One are available. Sign into the Google account you intend to check.

For illustrated setup instructions, use the **[Install guide on this project's GitHub Wiki](https://github.com/hoangsvit/google-ai/wiki/Install)**.

### Step 2 — Get the toolkit

Open **PowerShell** in the folder where you want to install the toolkit:

```powershell
git clone https://github.com/hoangsvit/google-ai.git
cd google-ai
.\run-all.ps1
```

If you already cloned the repository, update it before starting:

```powershell
git pull --ff-only
.\run-all.ps1
```

The no-argument command opens the Textual dashboard, installing its pinned dependency on first launch if needed. When you run a check, the environment helper can also install or locate ADB and the pinned Frida version. **You generally do not need to execute `setup_env.py` manually first.** Environment preparation may install tools or adjust Android/Frida/emulator settings.

If the terminal shows an ADB error, confirm that MuMu is running and Android debugging is enabled. Where ADB is on your PATH, you can verify the connection with:

```powershell
adb devices
```

The device must show as `device`, not `offline` or `unauthorized`. If ADB is not on PATH, let the toolkit locate/install Platform-Tools or follow the [detailed troubleshooting guide](docs/DETAILED-GUIDE.md).

## Use the dashboard (recommended)

### Start with Check Device & Offers

1. Click **Check Device & Offers** on the welcome screen. It invokes **Step 1 — Available offers**, intended to *list* offers rather than initiate checkout.
2. Watch **Live Status** for the stage, elapsed time, current activity and result. **Show technical details** reveals execution output. A warning after 30 seconds without new output indicates inactivity, **not proof of a hang**.
3. Check the account and offer information on the Android screen. A listed offer is **not** a guarantee of eligibility or a successful subscription.
4. Expand **Advanced: Run by step** only when you deliberately need to select a different stage.

**Important distinction:** Step 1 does not initiate a purchase, but underlying environment preflight can still install or repair ADB/Frida and change emulator/network settings. **Step 0 — Environment** is a setup/diagnostics stage, not a purchase-free guarantee of zero local side effects.

The sidebar lists the six stages. Android Device / Google Account cards update from observed output; account identifiers are masked. Original-author and maintainer credits link to their GitHub profiles in supported terminals.

### Advanced run modes

| Mode | Behavior |
| --- | --- |
| **One step only** | Runs only the selected Step **0–5**. |
| **From selected step** | Begins a guided checkout sequence at the chosen Step **2–5**, without replaying earlier checkout steps. |
| **All: Steps 2–5** | Begins the guided checkout sequence at **Step 2**. Step **5** is optional. |

All checkout stages on the dashboard require **explicit approval per stage**. After a stage returns `checkout_requested`, check the real Google Play subscription and renewal date. Only press **Verified in Google Play → Next** if the change has actually been verified. The next stage still requires separate approval. Failed or ambiguous results do not authorize advancing.

| Step | Purpose | Checkout risk |
| --- | --- | --- |
| **0 — Environment** | Diagnose/prepare Android, ADB and Frida | No subscription checkout; local/emulator changes possible |
| **1 — Available offers** | Query offers for the active Google Play account | No subscription checkout; preflight changes possible |
| **2 — Pro 12 months** | Original 12-month offer | **May start real checkout** |
| **3 — Pro +6 months** | Original subscription update | **May start real checkout** |
| **4 — Pro +6 months (second)** | Another original update | **May start real checkout** |
| **5 — Optional +6 months** | Optional original update | **May start real checkout** |

If Google Play already shows an active subscription, do **not** repeat Step 2. The names and durations of offers are historical labels, not guaranteed entitlements or extensions.

### Controls, Stop and Exit

While a stage is running, **Check Device & Offers**, Run, Run mode and Step selection are locked so another stage cannot be started. Help and technical details remain accessible.

- **Stop check (Steps 0–1):** requests cancellation of the local process tree. Cancellation can fail if a child process is stuck; inspect technical details.
- **Stop after this step (Steps 2–5):** prevents further stages, but **does not force-kill a checkout in progress**. The remote payment outcome could otherwise become unknown.
- **Exit toolkit / Q:** exits immediately while idle; during Steps 0–1 it requests cancellation and exits afterward, and during Steps 2–5 it queues exit after the current stage.
- **D** toggles technical details; **R** uses the selected advanced run mode. A **Next** button is available only for a reviewable checkout outcome in a guided sequence.

Neither Stop nor closing the terminal reverses an existing Google Play transaction. Always verify the real transaction and subscription status directly.

## PowerShell CLI (advanced)

The dashboard and the CLI reuse the same PowerShell/Python engine. Explicit command arguments bypass the TUI.

### Safe offer check and diagnostics

```powershell
.\run-all.ps1 -Step 1           # List offers; no checkout
.\run-all.ps1 -Step 1 -Debug    # Same check with technical diagnostics
.\run-all.ps1 -Step 0           # Environment diagnostics and setup
.\run-all.ps1 -Cli              # Legacy CLI, default Step 1
```

Local technical logs are stored under `logs/`, while fresh offer and stage reports are under `ultra0-report/`. **Do not share raw logs or full reports** without removing account identifiers and sensitive billing/purchase tokens.

The standalone `setup_env.py` and `setup-environment.bat` remain troubleshooting/repair tools, not mandatory steps before launching the dashboard.

### Checkout commands — may charge money

```powershell
.\run-all.ps1 -Step 2
.\run-all.ps1 -Step 3
.\run-all.ps1 -Step 4
.\run-all.ps1 -Step 5
```

**Unlike the TUI, an explicitly selected single checkout stage does not require a second typed PowerShell approval.** The original Python engine may automatically press Subscribe after checking the Google Play screen. Do not execute these commands unless you intend to initiate a potentially billable operation and have reviewed its terms.

To use the original **CLI** guided sequence:

```powershell
.\run-all.ps1 -AllStages
.\run-all.ps1 -AllStages -StartStep 3
```

The CLI performs its environment/offer checks and then proceeds through the original subscription stages, requesting numbered approvals between potentially billable operations (**1 = Continue, 2 = End run, 0 = Stop**). This differs from **All: Steps 2–5** on the TUI, which begins its guided sequence at Step 2. Starting the CLI sequence at Step 3 must only follow independent verification of an existing plan; it does not prove any prior extension succeeded.

Optional parameters:

```powershell
.\run-all.ps1 -Step 1 -Serial emulator-5554
.\run-all.ps1 -AllStages -Email "account@gmail.com"
```

Only use a `-Serial` observed through ADB. `-Email` constrains the account expected by the checks. `-Force` exists for compatibility but bypasses account-matching protections; **avoid using it**. It does not override Google Play payment restrictions or eligibility.

## Troubleshooting and results

| Problem or result | What to check |
| --- | --- |
| **MuMu / ADB not detected** | Install/start MuMu separately, enable root/ADB, verify the correct connected Android instance and authorization. |
| **Frida setup failure** | Review technical details; Frida **16.5.9** must be compatible with the host and device. |
| **No offers / `offer_query_failed`** | Open Google One and Google Play on the target Android instance and run Step 1 again. |
| **Account not verified / wrong account** | Inspect the active Google Play profile; do not bypass verification. |
| **`checkout_requested`** | Checkout was requested, **not verified as an active subscription**. Check Google Play directly. |
| **`already_subscribed` / `ineligible`** | Stop; do not retry other checkout stages based on unverified extension claims. |
| **Payment/security error (e.g. OR-REH-04)** | Follow Google Account/Payments security instructions. Do not repeatedly retry. |
| **Unicode output error** | Update the repository; the maintained Windows launcher configures Python UTF-8 output for piped status symbols. |

Verify subscription, payment amount, currency and renewal terms under **[Google Play Subscriptions](https://play.google.com/store/account/subscriptions)**. For advanced platform and Frida problems, see [Detailed setup and troubleshooting](docs/DETAILED-GUIDE.md).

**Platform support:** This README documents the Windows workflow. A macOS read-only prototype was closed without merging because it did not offer full feature parity. Do not assume the Windows checkout flow works on macOS.

## Documentation and contributing

- [Install guide — GitHub Wiki](https://github.com/hoangsvit/google-ai/wiki/Install)
- [Detailed setup and troubleshooting](docs/DETAILED-GUIDE.md)
- [Original author's stage and batch-file reference](docs/ORIGINAL-STEPS.md)
- [Historical author notes](docs/AUTHOR-NOTES.md)
- [Security and billing precautions](SECURITY.md)
- [Contributing](CONTRIBUTING.md) · [AI agent guidelines](AGENTS.md) · [Third-party notices](THIRD_PARTY_NOTICES.md)

GitHub Actions checks Python, PowerShell, Textual and mocked Frida/Billing behavior **without initiating real Google Play transactions**. Passing CI does not prove hardware compatibility or subscription eligibility.

## Credits

- **Original author:** [@gylive](https://github.com/gylive) — upstream [google-ultra](https://github.com/gylive/google-ultra), including the original Python/ADB/Frida/Google Play approach.
- **Maintainer:** [@hoangsvit](https://github.com/hoangsvit) / [ePlus.DEV](https://eplus.dev) — Windows/MuMu adaptation, terminal UI, compatibility fixes, tests and documentation.
- [Community contributors](https://github.com/hoangsvit/google-ai/graphs/contributors)

The upstream MIT notice is retained in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md); that notice does not independently license unrelated new contributions.
