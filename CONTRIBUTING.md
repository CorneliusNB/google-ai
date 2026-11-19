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

## Translations

The root [English README](README.md) is the maintained reference. Translated guides are [Vietnamese](README.vi.md), [Simplified Chinese](README.zh-CN.md), [Japanese](README.ja.md), [Korean](README.ko.md), [Spanish](README.es.md), and [French](README.fr.md).

When changing the installation requirements, stage/CLI behavior, or billing/security warnings, update all localized READMEs in the same PR. Keep PowerShell commands, code identifiers, original attribution, disclaimer links and safety boundaries identical in meaning. Do not translate executable flags or UI labels that remain in English. Run `python -m unittest discover -s tests -p 'test_readme_locales.py' -v` to check links and key safety text. Other detailed documentation is maintained in English unless explicitly localized.
