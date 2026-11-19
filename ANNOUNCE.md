# English release announcement drafts

These drafts intentionally describe the toolkit without guaranteeing a free subscription or eligibility.

## Short announcement

> **Google AI Android Toolkit**
>
> A Python + ADB + Frida research and diagnostics repository for inspecting Google Play promotional offer data in a rooted Android environment.
>
> Includes Android 15 Activity compatibility diagnostics, an English CLI, Windows PowerShell setup and mock tests.
>
> Offer data is not evidence that a trial is available, and the optional billing workflow can initiate a real subscription. Always verify pricing and renewal terms directly in Google Play.
>
> Repository: https://github.com/hoangsvit/google-ai

## Technical announcement

> The repository separates the Python entrypoint, Frida hook, bundled Android module, diagnostics and tests.
>
> Run `run-all.ps1 -ListOnly` to inspect the device and offer metadata without opening checkout. On supported environments, a guided workflow can optionally request a billing flow with explicit confirmations.
>
> The author's claims about stacking promotional periods have not been independently verified.

## One-line summary

> Android Google Play offer diagnostics (Python, ADB and Frida), with English documentation and read-only commands: https://github.com/hoangsvit/google-ai
