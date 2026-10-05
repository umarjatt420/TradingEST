from decimal import Decimal

from django.db import models


class Project(models.Model):
    """Master project / job — links to transactions by FK."""

    reference_number = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name="Reference #",
    )
    name = models.CharField(max_length=255, unique=True)
    client_name = models.CharField(max_length=255, blank=True)
    contract_value_excl_vat = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    advance_amount_incl_vat = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Client advance (incl. VAT)",
        help_text="Optional. Leave blank if client pays no advance.",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.reference_number} — {self.name}"

    @property
    def vat_15(self):
        """ROUND(contract × 0.15, 2) — Business-Logic §5 rule 2."""
        if self.contract_value_excl_vat is None:
            return None
        return (self.contract_value_excl_vat * Decimal("0.15")).quantize(Decimal("0.01"))

    @property
    def contract_incl_vat(self):
        if self.contract_value_excl_vat is None or self.vat_15 is None:
            return None
        return self.contract_value_excl_vat + self.vat_15

    @property
    def advance_percent_of_contract(self):
        """Advance as % of contract incl. VAT (auto-calculated from amount)."""
        amt = self.advance_amount_incl_vat
        contract = self.contract_incl_vat
        if amt is None or contract is None or contract == 0:
            return None
        return (amt / contract * Decimal("100")).quantize(Decimal("0.01"))

    @staticmethod
    def _format_percent(pct: Decimal) -> str:
        s = f"{pct:.2f}"
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s

    @property
    def client_advance_display(self):
        """Amount with auto-calculated % of contract incl. VAT."""
        from TradingEST.formatting import format_sar

        amt = self.advance_amount_incl_vat
        if amt is None:
            return None
        amt_str = format_sar(amt)
        pct = self.advance_percent_of_contract
        if pct is not None:
            return f"{amt_str} ({self._format_percent(pct)}%)"
        return amt_str
