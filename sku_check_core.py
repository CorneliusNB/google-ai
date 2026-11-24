"""Strict, token-free model for explicit read-only SKU inspection.

This module never touches Android, Frida, billing or user accounts.
"""
from __future__ import annotations

import re
from decimal import Decimal

SKU_RE = re.compile(r"^g1\.[a-z0-9][a-z0-9._-]{2,127}$")
ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
PERIOD_RE = re.compile(r"^P(?:\d+[YMWD]){1,4}$")
CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
MAX_SKUS = 10
MAX_OFFERS = 100
MAX_PHASES = 12


def validate_skus(values: list[str]) -> list[str]:
    if not values or len(values) > MAX_SKUS:
        raise ValueError("Select between 1 and 10 explicit product IDs")
    checked = []
    for value in values:
        if not isinstance(value, str) or not SKU_RE.fullmatch(value):
            raise ValueError("Invalid product ID: use g1. followed by letters, digits, dots, _ or -")
        if value not in checked:
            checked.append(value)
    return checked


def _id(value: object) -> str:
    return value if isinstance(value, str) and ID_RE.fullmatch(value) else ""


def _price(value: object) -> str | None:
    if isinstance(value, bool):
        return None
    value = str(value)
    if not value.isascii() or not value.isdecimal() or len(value) > 18:
        return None
    return str(int(value))


def _number(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        return None
    value = str(value)
    if not value.isascii() or not value.isdecimal() or len(value) > 5:
        return None
    return int(value)


def sanitize_offers(raw: object, requested: list[str]) -> dict:
    """Only allow safe IDs and complete phases; drop any token/account fields."""
    requested = validate_skus(requested)
    if not isinstance(raw, list):
        raise ValueError("Invalid offer response")
    offers = []
    seen = set()
    observed_products = set()
    products_without_offers = set()
    for row in raw[:MAX_OFFERS]:
        if not isinstance(row, dict):
            continue
        product = row.get("sku")
        if product not in requested:
            continue
        observed_products.add(product)
        if row.get("no_offers") is True:
            products_without_offers.add(product)
            continue
        offer = _id(row.get("offer_id"))
        base_plan = _id(row.get("base_plan_id"))
        # Subscription offers may have an empty offer ID for base plans.
        if not base_plan:
            continue
        phases = []
        for ph in (row.get("phases") if isinstance(row.get("phases"), list) else [])[:MAX_PHASES]:
            if not isinstance(ph, dict):
                continue
            micros = _price(ph.get("price_amount_micros"))
            currency = ph.get("currency")
            period = ph.get("billing_period")
            if (micros is None or not isinstance(currency, str) or
                    not CURRENCY_RE.fullmatch(currency) or
                    not isinstance(period, str) or not PERIOD_RE.fullmatch(period)):
                continue
            phases.append({
                "price_amount_micros": micros,
                "currency": currency,
                "billing_period": period,
                "billing_cycle_count": _number(ph.get("billing_cycle_count")),
                "recurrence_mode": _number(ph.get("recurrence_mode")),
            })
        if not phases:
            continue
        key = (product, base_plan, offer)
        if key in seen:
            continue
        seen.add(key)
        offers.append({
            "sku": product, "offer_id": offer, "base_plan_id": base_plan,
            "phases": phases,
            "eligibility_verified": False, "subscription_active_verified": False,
        })
    return {
        "status": "observed" if offers else ("no_offers" if products_without_offers else "not_returned"),
        "items": offers,
        "missing_skus": [sku for sku in requested if sku not in observed_products],
        "eligibility_verified": False,
        "subscription_active_verified": False,
    }


def render_result(result: dict) -> str:
    """Compact terminal-friendly summary; never render raw inputs or payloads."""
    status = result.get("status", "query_error")
    if status != "observed":
        messages = {
            "not_returned": "Google Play returned no matching product metadata.",
            "no_offers": "Product details returned, but no subscription offers were listed.",
            "account_unverified": "Play account not verified. Recheck Step 1.",
            "device_not_ready": "Device/Google One/Frida is not ready. Check Step 1.",
            "billing_unavailable": "BillingClient did not return data.",
            "timeout": "The read-only SKU query timed out.",
            "cancelled": "SKU query cancelled.",
            "query_error": "Could not complete SKU query. Check device and try again.",
        }
        return messages.get(status, "SKU metadata is unavailable.")
    lines = ["OBSERVED OFFERS (NOT ELIGIBILITY)"]
    for row in result.get("items", [])[:MAX_OFFERS]:
        lines.append(f"{row['sku']}  /  {row['base_plan_id']}  /  {row['offer_id'] or '(base)'}")
        for index, phase in enumerate(row["phases"][:MAX_PHASES], 1):
            amt = Decimal(phase["price_amount_micros"]) / Decimal(1_000_000)
            lines.append(f"  Phase {index}: {amt:,.2f} {phase['currency']} / {phase['billing_period']}")
    lines.append("Eligibility: UNVERIFIED  |  Subscription: UNVERIFIED")
    lines.append("No purchase, checkout, or subscription changes were requested.")
    return "\n".join(lines)
