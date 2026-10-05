"""
Derived metrics — mirrors Business-Logic.md Accounts_Summary, Tax Report,
Monthly_Report, and Dashboard.
Uses ORM aggregates with Q(), Sum(), filter= on aggregate.
"""

from __future__ import annotations

import calendar
from datetime import date
from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Max, Q, Sum, Value
from django.db.models.functions import Coalesce

from projects.models import Project
from transactions.models import FlowType, PaymentStatus, Transaction


def paid_status_q(prefix: str = "") -> Q:
    """
    Project income & tax sales: only fully Paid (excludes Partially Paid).
    Use prefix 'transactions__' for Project aggregates.
    """
    key = f"{prefix}payment_status__iexact"
    return Q(**{key: PaymentStatus.PAID.value})


def month_bounds(year: int, month: int) -> tuple[date, date]:
    """[start, end_exclusive) for calendar month."""
    start = date(year, month, 1)
    if month == 12:
        end_exc = date(year + 1, 1, 1)
    else:
        end_exc = date(year, month + 1, 1)
    return start, end_exc


def _sum_total_amount(qs):
    v = qs.aggregate(s=Sum("total_amount"))["s"]
    return v if v is not None else Decimal("0")


def _sum_amount_excl(qs):
    v = qs.aggregate(s=Sum("amount_excl_vat"))["s"]
    return v if v is not None else Decimal("0")


def _sum_tax_amount(qs):
    v = qs.aggregate(s=Sum("tax_amount"))["s"]
    return v if v is not None else Decimal("0")


def has_vat_q(prefix: str = "") -> Q:
    """Tax % or Tax Amount > 0 (exclude 0% from tax report purchase totals)."""
    tax_amt = f"{prefix}tax_amount__gt"
    tax_pct = f"{prefix}tax_percent__gt"
    return Q(**{tax_amt: 0}) | Q(**{tax_pct: 0})


def accounts_summary_rows():
    """
    Rows match Accounts_Summary sheet — VAT-inclusive (P) for Cash/Bank/Owner Contribution;
    amount excl. (D) for Owner Drawings through Employee Advance.
    """
    tx = Transaction.objects.all()

    def pair_total_p(account: str):
        inn = _sum_total_amount(
            tx.filter(account__iexact=account.strip(), flow_type=FlowType.IN)
        )
        out = _sum_total_amount(
            tx.filter(account__iexact=account.strip(), flow_type=FlowType.OUT)
        )
        return inn, out, inn - out

    def pair_owner_drawings():
        od = Q(category__iexact="Owner Drawings") | Q(account__iexact="Owner Drawings")
        inn = _sum_amount_excl(tx.filter(od, flow_type=FlowType.IN))
        out = _sum_amount_excl(tx.filter(od, flow_type=FlowType.OUT))
        return inn, out, inn - out

    def pair_account_d(account: str):
        inn = _sum_amount_excl(
            tx.filter(account__iexact=account.strip(), flow_type=FlowType.IN)
        )
        out = _sum_amount_excl(
            tx.filter(account__iexact=account.strip(), flow_type=FlowType.OUT)
        )
        return inn, out, inn - out

    rows = []
    for label, inn, out, bal, note in [
        ("Cash", *pair_total_p("Cash"), "With VAT"),
        ("Bank", *pair_total_p("Bank"), "With VAT"),
        ("Owner Contribution", *pair_total_p("Owner Contribution"), "With VAT"),
        ("Owner Drawings", *pair_owner_drawings(), "Without VAT"),
        (
            "Accounts Receivable",
            *pair_account_d("Accounts Receivable"),
            "Without VAT",
        ),
        (
            "Accounts Payable",
            *pair_account_d("Accounts Payable"),
            "Without VAT",
        ),
        (
            "Employee Payable",
            *pair_account_d("Employee Payable"),
            "Without VAT",
        ),
        (
            "Employee Advance",
            *pair_account_d("Employee Advance"),
            "Without VAT",
        ),
    ]:
        rows.append(
            {
                "label": label,
                "total_in": inn,
                "total_out": out,
                "balance": bal,
                "note": note,
            }
        )
    return rows


def accounts_summary_map():
    """Label → row dict for dashboard lookups."""
    return {r["label"]: r for r in accounts_summary_rows()}


def months_in_period(end_year: int, end_month: int, months_count: int) -> list[tuple[int, int]]:
    """Chronological list of (year, month) ending at end_month (inclusive)."""
    if months_count < 1:
        months_count = 1
    y, m = end_year, end_month
    collected: list[tuple[int, int]] = []
    for _ in range(months_count):
        collected.append((y, m))
        m -= 1
        if m < 1:
            m = 12
            y -= 1
    collected.reverse()
    return collected


def month_display_name(year: int, month: int) -> str:
    return f"{calendar.month_name[month]} {year}"


def tax_report_for_month(year: int, month: int) -> dict:
    """
    Tax Report — Business-Logic §3 Tax Report + rule 10–12.
    Sales: IN, Client, Paid (Output VAT = sum Tax Amount).
    Purchases: OUT, Cash with VAT only in Total Purchases (0% lines excluded).
    """
    start, end_exc = month_bounds(year, month)
    base = Transaction.objects.filter(date__gte=start, date__lt=end_exc)

    sales_q = (
        Q(flow_type=FlowType.IN)
        & Q(party_type__iexact="client")
        & paid_status_q()
    )
    sales_base = base.filter(sales_q)

    total_sales_excl = _sum_amount_excl(sales_base)
    output_vat = _sum_tax_amount(sales_base)

    purch_q = Q(flow_type=FlowType.OUT) & Q(account__iexact="cash")
    purch_vatable = base.filter(purch_q).filter(has_vat_q())
    total_purchases_excl = _sum_amount_excl(purch_vatable)
    input_vat = _sum_tax_amount(purch_vatable)

    if total_sales_excl == Decimal("0") and total_purchases_excl == Decimal("0"):
        net_vat = None
    else:
        net_vat = output_vat - input_vat

    return {
        "year": year,
        "month": month,
        "month_name": month_display_name(year, month),
        "total_sales_excl_vat": total_sales_excl,
        "output_vat": output_vat,
        "total_purchases_excl_vat": total_purchases_excl,
        "input_vat": input_vat,
        "net_vat_payable": net_vat,
    }


def tax_report_for_period(end_year: int, end_month: int, months_count: int) -> dict:
    """Tax report for N months ending at end_year/end_month (1–12 months)."""
    months_count = max(1, min(12, int(months_count)))
    period_months = months_in_period(end_year, end_month, months_count)
    rows = [tax_report_for_month(y, m) for y, m in period_months]

    total_sales = sum((r["total_sales_excl_vat"] for r in rows), Decimal("0"))
    output_vat = sum((r["output_vat"] for r in rows), Decimal("0"))
    total_purch = sum((r["total_purchases_excl_vat"] for r in rows), Decimal("0"))
    input_vat = sum((r["input_vat"] for r in rows), Decimal("0"))

    if total_sales == Decimal("0") and total_purch == Decimal("0"):
        net_vat = None
    else:
        net_vat = output_vat - input_vat

    month_names = [r["month_name"] for r in rows]
    first_name = month_names[0]
    last_name = month_names[-1]
    period_label = first_name if len(rows) == 1 else f"{first_name} – {last_name}"

    return {
        "end_year": end_year,
        "end_month": end_month,
        "months_count": months_count,
        "period_label": period_label,
        "month_names": month_names,
        "month_names_line": ", ".join(month_names),
        "rows": rows,
        "months": rows,
        "totals": {
            "month_name": "Total",
            "total_sales_excl_vat": total_sales,
            "output_vat": output_vat,
            "total_purchases_excl_vat": total_purch,
            "input_vat": input_vat,
            "net_vat_payable": net_vat,
        },
    }


def monthly_report_for_month(year: int, month: int) -> dict:
    """
    Monthly_Report — cash IN/OUT on amount excl.; category splits; credit sales.
    """
    start, end_exc = month_bounds(year, month)
    base = Transaction.objects.filter(date__gte=start, date__lt=end_exc)

    cash_in = base.filter(flow_type=FlowType.IN, account__iexact="cash")
    cash_out = base.filter(flow_type=FlowType.OUT, account__iexact="cash")

    total_income_excl = _sum_amount_excl(cash_in)
    total_expense_excl = _sum_amount_excl(cash_out)
    net_pl = total_income_excl - total_expense_excl

    def cat_sum(name: str):
        return _sum_amount_excl(cash_out.filter(category=name))

    credit_sale = _sum_amount_excl(
        base.filter(flow_type=FlowType.IN, account__iexact="accounts receivable")
    )

    return {
        "year": year,
        "month": month,
        "total_income_excl_vat": total_income_excl,
        "total_expense_excl_vat": total_expense_excl,
        "net_profit_loss": net_pl,
        "material_expense": cat_sum("Material Purchase"),
        "food_expense": cat_sum("Food Expense"),
        "fuel_expense": cat_sum("Fuel Expense"),
        "labour_expense": cat_sum("Labour Expense"),
        "transport_expense": cat_sum("Transport Expense"),
        "credit_sale": credit_sale,
    }


def total_net_profit_all_projects() -> Decimal:
    """
    SUM(Projects Net Profit) — Net = Contract excl. − Total Expense (OUT sum).
    Null contract treated as 0 for the sum (Excel-range parity).
    """
    rows = Project.objects.annotate(
        total_expense=Sum(
            "transactions__total_amount",
            filter=Q(transactions__flow_type=FlowType.OUT),
        ),
    ).annotate(
        net_line=ExpressionWrapper(
            Coalesce(F("contract_value_excl_vat"), Value(Decimal("0")))
            - Coalesce(F("total_expense"), Value(Decimal("0"))),
            output_field=DecimalField(max_digits=18, decimal_places=2),
        )
    )
    agg = rows.aggregate(total=Sum("net_line"))
    return agg["total"] if agg["total"] is not None else Decimal("0")


def latest_transaction_month() -> tuple[int, int] | None:
    """Returns (year, month) of max transaction date, or None."""
    r = Transaction.objects.aggregate(mx=Max("date"))
    d = r["mx"]
    if d is None:
        return None
    return d.year, d.month


def dashboard_metrics(vat_year: int, vat_month: int):
    """Dashboard KPIs + VAT for selected period (Excel ties latest VAT to Tax Report row 2)."""
    smap = accounts_summary_map()

    def bal(label: str) -> Decimal:
        return smap[label]["balance"]

    owner_net = bal("Owner Contribution") - bal("Owner Drawings")

    vat = tax_report_for_month(vat_year, vat_month)

    return {
        "cash_balance": bal("Cash"),
        "bank_balance": bal("Bank"),
        "owner_net_drawings": owner_net,
        "accounts_receivable": bal("Accounts Receivable"),
        "accounts_payable": bal("Accounts Payable"),
        "employee_payable": bal("Employee Payable"),
        "employee_advance": bal("Employee Advance"),
        "total_net_profit_projects": total_net_profit_all_projects(),
        "net_vat_payable": vat["net_vat_payable"],
        "vat_period_label": f"{vat_month:02d}/{vat_year}",
    }
