from datetime import date
from decimal import Decimal

from django.test import TestCase

from reports.services import tax_report_for_month
from transactions.models import FlowType, Transaction


class TaxReportPurchasesTest(TestCase):
    def test_input_vat_excludes_zero_vat_cash_out(self):
        """May 2026-style: taxable purchase + 0% salary — purchases total matches VAT base."""
        Transaction.objects.create(
            reference_number="TEST-DRILL-1",
            date=date(2026, 5, 23),
            description="Drill bit purchased",
            flow_type=FlowType.OUT,
            amount_excl_vat=Decimal("80"),
            account="Cash",
            category="Material Purchase",
            tax_percent=Decimal("15"),
            party_type="Supplier",
            payment_status="Paid",
        )
        Transaction.objects.create(
            reference_number="TEST-SALARY-1",
            date=date(2026, 5, 23),
            description="Salary paid to Abdullah",
            flow_type=FlowType.OUT,
            amount_excl_vat=Decimal("1700"),
            account="Cash",
            category="Salary",
            tax_percent=Decimal("0"),
            party_type="Employee",
            payment_status="Paid",
        )

        report = tax_report_for_month(2026, 5)
        self.assertEqual(report["total_purchases_excl_vat"], Decimal("80"))
        self.assertEqual(report["input_vat"], Decimal("12"))
