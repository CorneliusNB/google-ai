# Contributing

Thanks for helping improve this Windows/MuMu adaptation. The original implementation comes from [gylive/google-ultra](https://github.com/gylive/google-ultra); current maintenance is by [David Nguyen (@hoangsvit)](https://github.com/hoangsvit).

## Report an issue

Use [GitHub Issues](https://github.com/hoangsvit/google-ai/issues) and include the command, Windows/Android version, relevant non-sensitive errors, and steps to reproduce. **Redact** Google account emails, passwords, payment details, offer/purchase tokens, device identifiers, and local credentials.

## Propose a change

Open a [pull request](https://github.com/hoangsvit/google-ai/pulls) with one focused improvement. Keep the original step mappings intact, explain any behavior change, and add mock tests for fixes. Do not run live subscription checkout in CI.

Before opening the PR, run:

```powershell
python -m unittest discover -s tests -v
```

Documentation and terminal usability fixes are welcome. Preserve attribution to upstream authors and retain their MIT notice.
