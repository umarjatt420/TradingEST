"""Category choices for transactions — defaults plus persisted custom names."""

from .models import LedgerCategory, Transaction, TransactionCategory

ADD_CATEGORY_VALUE = "__add_category__"
ADD_CATEGORY_LABEL = "+ Add category"


def normalize_category_name(raw: str | None) -> str:
    return " ".join(str(raw or "").strip().split())


def ensure_category_exists(name: str) -> str:
    """Save category to the registry so it appears on future forms."""
    normalized = normalize_category_name(name)
    if not normalized:
        return ""
    TransactionCategory.objects.get_or_create(name=normalized)
    return normalized


def all_category_names() -> list[str]:
    defaults = [choice.value for choice in LedgerCategory]
    stored = TransactionCategory.objects.values_list("name", flat=True)
    from_transactions = (
        Transaction.objects.exclude(category="")
        .values_list("category", flat=True)
        .distinct()
    )
    return sorted(set(defaults) | set(stored) | set(from_transactions), key=str.casefold)


def category_field_choices(include_blank: bool = True) -> list[tuple[str, str]]:
    choices = [(name, name) for name in all_category_names()]
    if include_blank:
        return [("", "---------")] + choices
    return choices
