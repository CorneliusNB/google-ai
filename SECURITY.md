# Security and responsible use

This repository is an independent, unaudited research project, **not affiliated with Google**. The included Android/Frida tooling runs with elevated privileges and accesses a Google Play database. Its bundled DEX module has not undergone a full independent security audit.

## Important guardrails

- Treat offer visibility as informational only. Subscription eligibility, promotional duration, billing, renewal dates, and prices are determined by Google Play.
- Checkout creation (`launchBillingFlow()` return code 0) is **not** proof of a successful purchase or entitlement. The script deliberately does not auto-tap Subscribe. Verify the subscription and billing date manually after a legitimate transaction.
- Never use an account or payment method you do not control or have explicit authorization to test. Do not use the tool to misrepresent eligibility or bypass terms.
- Keep Google credentials, recovery codes, TOTP seeds, card numbers, and CVC outside of this repository. Do not commit raw data files, Play databases, offers/purchase tokens, or reports.
- Review downloaded Frida executables and the included BillingClient DEX before running on a real device. Do not run this on your primary Android device or main Google account.
- `--force` is restricted to read-only offer listing. Purchase operations require a verified Play account.
- Reading a purchase token from Play's database can fail if database schema/location changes or if the account isn't active. Such failures intentionally abort the replacement flow.
- Network settings are not modified by default. `--reset-network` explicitly opts into changing device proxy settings and stopping Clash variants.

## Reporting vulnerabilities

Please report sensitive findings privately to the repository owner. Avoid filing issues containing personal credentials, payment data, offer tokens, or Play purchase tokens.

## Testing boundaries

The provided test suite mocks ADB/Frida and uses disposable SQLite fixtures. It does not validate Google Play billing transactions, promotion eligibility, or subscription durations.
