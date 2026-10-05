from decimal import Decimal

from django.db import models


class FlowType(models.TextChoices):
    IN = "IN", "IN"
    OUT = "OUT", "OUT"


class PaymentStatus(models.TextChoices):
    PAID = "Paid", "Paid"
    PARTIALLY_PAID = "Partially Paid", "Partially Paid"
    CREDIT = "Credit", "Credit"
    UNPAID = "Unpaid", "Unpaid"


class LedgerAccount(models.TextChoices):
    CASH = "Cash", "Cash"
    BANK = "Bank", "Bank"
    ACCOUNTS_RECEIVABLE = "Accounts Receivable", "Accounts Receivable"
    ACCOUNTS_PAYABLE = "Accounts Payable", "Accounts Payable"
    EMPLOYEE_ADVANCE = "Employee Advance", "Employee Advance"
    EMPLOYEE_PAYABLE = "Employee Payable", "Employee Payable"
    OWNER_CONTRIBUTION = "Owner Contribution", "Owner Contribution"
    OWNER_DRAWINGS = "Owner Drawings", "Owner Drawings"


class LedgerCategory(models.TextChoices):
    MATERIAL_PURCHASE = "Material Purchase", "Material Purchase"
    PROJECT_INCOME = "Project Income", "Project Income"
    FOOD_EXPENSE = "Food Expense", "Food Expense"
    FUEL_EXPENSE = "Fuel Expense", "Fuel Expense"
    LABOUR_EXPENSE = "Labour Expense", "Labour Expense"
    TRANSPORT_EXPENSE = "Transport Expense", "Transport Expense"
    OWNER_DRAWINGS = "Owner Drawings", "Owner Drawings"
    SALARY = "Salary", "Salary"


class PartyType(models.TextChoices):
    CLIENT = "Client", "Client"
    SUPPLIER = "Supplier", "Supplier"
    EMPLOYEE = "Employee", "Employee"
    OWNER = "Owner", "Owner"


class TransactionCategory(models.Model):
    """User-defined and default transaction categories (persisted for dropdowns)."""

    name = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Transaction categories"

    def __str__(self):
        return self.name


def normalize_payment_status(raw: str | None) -> str:
    """Strip + match controlled vocabulary (case-insensitive)."""
    if not raw:
        return ""
    s = str(raw).strip()
    if not s:
        return ""
    low = s.lower()
    for ps in PaymentStatus:
        if ps.value.lower() == low:
            return ps.value
    return s.title()


class Transaction(models.Model):
    """
    Ledger line — mirrors Excel Transactions sheet.
    Tax Amount / Total Amount follow Business-Logic §5 rule 1.
    """

    reference_number = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name="Reference #",
    )
    date = models.DateField(db_index=True)
    description = models.CharField(max_length=500, blank=True)
    flow_type = models.CharField(max_length=3, choices=FlowType.choices, db_index=True)
    amount_excl_vat = models.DecimalField(max_digits=14, decimal_places=2)
    account = models.CharField(
        max_length=64,
        db_index=True,
        choices=LedgerAccount.choices,
    )
    category = models.CharField(max_length=128, db_index=True)
    project = models.ForeignKey(
        "projects.Project",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="transactions",
    )
    qty = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    rate = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    party_name = models.CharField(max_length=255, blank=True)
    party_type = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        choices=PartyType.choices,
    )
    invoice_number = models.CharField(max_length=128, blank=True)
    tax_percent = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    payment_status = models.CharField(
        max_length=64,
        blank=True,
        choices=PaymentStatus.choices,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-pk"]
        indexes = [
            models.Index(fields=["date", "flow_type"]),
            models.Index(fields=["account", "flow_type"]),
        ]

    def __str__(self):
        return f"{self.reference_number} · {self.date} {self.flow_type} {self.amount_excl_vat}"

    def compute_tax_and_total(self):
        """Excel: O = ROUND(D×N/100,2) when both present; P = D + O when D present."""
        if self.amount_excl_vat is not None and self.tax_percent is not None:
            self.tax_amount = (
                self.amount_excl_vat * self.tax_percent / Decimal("100")
            ).quantize(Decimal("0.01"))
        else:
            self.tax_amount = None
        if self.amount_excl_vat is not None:
            self.total_amount = self.amount_excl_vat + (
                self.tax_amount if self.tax_amount is not None else Decimal("0")
            )
        else:
            self.total_amount = None

    def save(self, *args, **kwargs):
        if self.payment_status:
            self.payment_status = normalize_payment_status(self.payment_status)
        self.compute_tax_and_total()
        super().save(*args, **kwargs)


class LegacyPayable(models.Model):
    """Old Accounts Payable — isolated legacy supplier balances."""

    supplier_name = models.CharField(max_length=255)
    total_payable = models.DecimalField(max_digits=14, decimal_places=2)
    total_paid = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    date_last_paid = models.DateField(null=True, blank=True)
    projects_name = models.CharField(max_length=255, blank=True)
    status_note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["supplier_name", "pk"]
        verbose_name = "Legacy payable"
        verbose_name_plural = "Legacy payables"

    def __str__(self):
        return self.supplier_name

    @property
    def remaining(self):
        return self.total_payable - self.total_paid
