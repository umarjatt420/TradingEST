from decimal import Decimal

from django.db import models


class SalaryType(models.TextChoices):
    MONTHLY = "Monthly", "Monthly"
    DAILY = "Daily", "Daily"
    WEEKLY = "Weekly", "Weekly"


class Employee(models.Model):
    name = models.CharField(max_length=255)
    salary_paid_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Payment date",
        help_text="Date when salary was paid to this employee.",
    )
    salary_type = models.CharField(
        max_length=16, choices=SalaryType.choices, default=SalaryType.MONTHLY
    )
    monthly_salary = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    daily_rate = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    days_worked = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    salary_paid_this_month = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    advance_taken = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    advance_adjusted = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    previous_pending_salary = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def salary_due_this_month(self):
        """
        IFERROR nested IF: Monthly → C; Daily → D×E; Weekly → C; else 0.
        """
        st = self.salary_type
        if st == SalaryType.MONTHLY or st == SalaryType.WEEKLY:
            return self.monthly_salary or Decimal("0")
        if st == SalaryType.DAILY:
            dr = self.daily_rate or Decimal("0")
            dw = self.days_worked or Decimal("0")
            return dr * dw
        return Decimal("0")

    @property
    def pending_salary_this_month(self):
        due = self.salary_due_this_month
        paid = self.salary_paid_this_month
        if paid is None:
            paid = Decimal("0")
        return due - paid

    @property
    def advance_balance(self):
        taken = self.advance_taken or Decimal("0")
        adj = self.advance_adjusted or Decimal("0")
        return taken - adj

    @property
    def total_pending_salary_all_months(self):
        prev = self.previous_pending_salary or Decimal("0")
        return self.pending_salary_this_month + prev
