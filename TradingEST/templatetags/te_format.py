from django import template

from TradingEST.formatting import format_number, format_sar

register = template.Library()


@register.filter
def sar(value):
    """Format as SAR 1,234.56; None/empty → em dash."""
    out = format_sar(value)
    return out if out is not None else "—"


@register.filter
def num(value):
    """Format as 1,234.56 (quantities, rates, percentages); None/empty → em dash."""
    out = format_number(value)
    return out if out is not None else "—"
