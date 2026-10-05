"""Shared numeric formatting for money and quantities."""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

_TWOPLACES = Decimal("0.01")


def _to_decimal(value) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        d = value if isinstance(value, Decimal) else Decimal(str(value))
        return d.quantize(_TWOPLACES, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        return None


def format_number(value) -> str | None:
    """Comma-separated number with exactly 2 decimal places (no currency prefix)."""
    d = _to_decimal(value)
    if d is None:
        return None
    return f"{d:,.2f}"


def format_sar(value) -> str | None:
    """SAR-prefixed money string, e.g. SAR 1,500.00."""
    n = format_number(value)
    if n is None:
        return None
    return f"SAR {n}"


def format_sar_or(value, placeholder: str = "—") -> str:
    return format_sar(value) or placeholder
