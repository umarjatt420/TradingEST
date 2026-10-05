from django import template

from transactions.display_labels import TRANSACTION_FIELD_LABELS

register = template.Library()


def _tx_label_text(field_name: str) -> str:
    return TRANSACTION_FIELD_LABELS.get(
        field_name,
        str(field_name).replace("_", " ").title(),
    )


@register.filter
def tx_label(field_name: str) -> str:
    """Title-case transaction field label (form, detail, list)."""
    return _tx_label_text(field_name)


@register.simple_tag
def tx_label_tag(field_name: str) -> str:
    return _tx_label_text(field_name)
