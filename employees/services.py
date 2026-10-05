from django.db.models import F, OuterRef, QuerySet, Subquery
from django.db.models.functions import Coalesce

from transactions.models import FlowType, LedgerCategory, Transaction

from .models import Employee


def _latest_salary_payment_subquery():
    return (
        Transaction.objects.filter(
            category=LedgerCategory.SALARY,
            flow_type=FlowType.OUT,
            party_name__iexact=OuterRef("name"),
        )
        .order_by("-date", "-pk")
        .values("date")[:1]
    )


def employees_with_paid_on(queryset: QuerySet[Employee] | None = None) -> QuerySet[Employee]:
    """Annotate paid_on = manual payment date, else latest salary transaction date."""
    if queryset is None:
        queryset = Employee.objects.all()
    return queryset.annotate(
        paid_on=Coalesce(
            F("salary_paid_date"),
            Subquery(_latest_salary_payment_subquery()),
        )
    )


def sync_employee_from_salary_transaction(txn: Transaction) -> None:
    """Keep employee payment date/amount in sync when a salary OUT line is saved."""
    if txn.category != LedgerCategory.SALARY or txn.flow_type != FlowType.OUT:
        return
    party = (txn.party_name or "").strip()
    if not party:
        return
    amount = txn.total_amount if txn.total_amount is not None else txn.amount_excl_vat
    Employee.objects.filter(name__iexact=party).update(
        salary_paid_date=txn.date,
        salary_paid_this_month=amount,
    )
