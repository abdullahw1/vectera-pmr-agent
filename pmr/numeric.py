"""Exact currency at computation boundaries; explicit rounding only for display.

JSON stores Decimal as base-ten strings, never binary floating-point approximations.
Rates remain supplied ratios; they are not recalculated from rounded cash flows.
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import math

MONEY_KEYS = {
    "nav",
    "commitment",
    "funded",
    "unfunded",
    "plan",
    "target",
    "beginning",
    "contributions",
    "distributions",
    "withdrawals",
    "income",
    "fees",
    "appreciation",
    "ending",
    "contribution",
    "approved_total",
    "amount",
}
MONEY_HEADERS = {
    "market value dollars",
    "commitment amount",
    "funded amount",
    "unfunded commitments",
    "beginning market value dollars",
    "contributions",
    "distributions",
    "withdrawals",
    "gross income",
    "manager fees",
    "appreciation",
}


def currency(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal, str)):
        raise ValueError("Currency must be a finite base-ten number")
    try:
        result = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError("Invalid currency") from error
    if not result.is_finite() or result != result.quantize(Decimal("0.01")):
        raise ValueError("Currency must be finite with no fractions of a cent")
    return result


def finite_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("Expected a finite number (not a boolean)")
    return float(value)


def display(value, places=1):
    result = Decimal(str(value)).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    return f"{result:,.{places}f}"


def restore_money(data):
    """Rehydrate only known currency fields, not history's explicitly USD-million series."""
    for record in [data["portfolio"], *data["funds"], *data["sleeves"].values()]:
        for key in MONEY_KEYS & record.keys():
            if record[key] is not None:
                record[key] = currency(record[key])
    for events in data["activity"].values():
        for event in events:
            if event.get("amount") is not None:
                event["amount"] = currency(event["amount"])
    return data
