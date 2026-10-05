import uuid
from decimal import Decimal

from django import forms

from projects.models import Project

from .category_utils import (
    ADD_CATEGORY_VALUE,
    category_field_choices,
    ensure_category_exists,
    normalize_category_name,
)
from .display_labels import apply_transaction_field_labels
from .models import LegacyPayable, Transaction


class TransactionForm(forms.ModelForm):
    project_reference = forms.ModelChoiceField(
        queryset=Project.objects.none(),
        label="Reference #",
        required=False,
        empty_label="—",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Transaction
        fields = [
            "date",
            "description",
            "flow_type",
            "amount_excl_vat",
            "account",
            "category",
            "project",
            "qty",
            "rate",
            "party_name",
            "party_type",
            "invoice_number",
            "tax_percent",
            "payment_status",
            "notes",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "flow_type": forms.Select(attrs={"class": "form-select"}),
            "amount_excl_vat": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "account": forms.Select(attrs={"class": "form-select"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "project": forms.Select(attrs={"class": "form-select"}),
            "qty": forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
            "rate": forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
            "party_name": forms.TextInput(attrs={"class": "form-control"}),
            "party_type": forms.Select(attrs={"class": "form-select"}),
            "invoice_number": forms.TextInput(attrs={"class": "form-control"}),
            "tax_percent": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "payment_status": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Newest projects first so recently added refs (e.g. ss3486) are easy to find
        projects = Project.objects.order_by("-pk")
        self.fields["project_reference"].queryset = projects
        self.fields["project"].queryset = projects
        self.fields["project_reference"].label_from_instance = lambda obj: obj.reference_number
        self.fields["project"].label_from_instance = lambda obj: obj.name
        self.fields["project"].required = False
        self.fields["project"].empty_label = "—"
        self.fields["payment_status"].required = True
        self.fields["amount_excl_vat"].required = True
        if not self.instance.pk:
            self.fields["invoice_number"].required = True
        self.fields["party_type"].required = False
        self.fields["party_type"].empty_label = "—"

        if self.instance.pk and self.instance.project_id:
            self.fields["project_reference"].initial = self.instance.project_id
            self.fields["project"].initial = self.instance.project_id

        category_choices = category_field_choices()
        existing = {value for value, _ in category_choices if value}
        if self.instance.pk and self.instance.category:
            if self.instance.category not in existing:
                category_choices.append((self.instance.category, self.instance.category))
                existing.add(self.instance.category)
        posted_category = ""
        if self.data:
            posted_category = normalize_category_name(self.data.get("category"))
        if posted_category and posted_category not in existing:
            category_choices.append((posted_category, posted_category))
        self.fields["category"] = forms.ChoiceField(
            choices=category_choices,
            required=True,
            widget=forms.Select(attrs={"class": "form-select", "id": "id_category"}),
        )
        if self.instance.pk and self.instance.category:
            self.fields["category"].initial = self.instance.category

        self.order_fields(
            [
                "project_reference",
                "project",
                "date",
                "description",
                "flow_type",
                "amount_excl_vat",
                "account",
                "category",
                "qty",
                "rate",
                "party_name",
                "party_type",
                "invoice_number",
                "tax_percent",
                "payment_status",
                "notes",
            ]
        )
        apply_transaction_field_labels(self)

    def clean(self):
        cleaned = super().clean()
        proj_ref = cleaned.get("project_reference")
        proj = cleaned.get("project")

        if proj_ref and proj and proj_ref.pk != proj.pk:
            self.add_error(
                None,
                "Reference # and Project Name must select the same project.",
            )
        elif proj_ref and not proj:
            cleaned["project"] = proj_ref
        elif proj and not proj_ref:
            cleaned["project_reference"] = proj

        amt = cleaned.get("amount_excl_vat")
        if amt is None:
            self.add_error("amount_excl_vat", "Amount (excl. VAT) is required.")
        elif amt <= Decimal("0"):
            self.add_error("amount_excl_vat", "Amount must be greater than zero.")

        tp = cleaned.get("tax_percent")
        if tp is not None:
            if tp < Decimal("0") or tp > Decimal("100"):
                self.add_error("tax_percent", "Tax % must be between 0 and 100.")

        if not cleaned.get("payment_status"):
            self.add_error("payment_status", "Payment status is required.")

        invoice = (cleaned.get("invoice_number") or "").strip()
        if not self.instance.pk and not invoice:
            self.add_error("invoice_number", "Invoice number is required.")
        else:
            cleaned["invoice_number"] = invoice

        category = cleaned.get("category")
        if category == ADD_CATEGORY_VALUE:
            self.add_error("category", "Select a category or click + Add category.")
        elif not category:
            self.add_error("category", "Category is required.")
        else:
            cleaned["category"] = ensure_category_exists(category)

        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.project = self.cleaned_data.get("project") or self.cleaned_data.get(
            "project_reference"
        )

        creating = instance.pk is None
        if creating and not instance.reference_number:
            instance.reference_number = f"TXN-TMP-{uuid.uuid4().hex[:12]}"

        if commit:
            instance.save()
            if creating and instance.reference_number.startswith("TXN-TMP-"):
                instance.reference_number = f"TXN-{instance.pk:06d}"
                instance.save(update_fields=["reference_number"])
        return instance


class LegacyPayableForm(forms.ModelForm):
    class Meta:
        model = LegacyPayable
        fields = [
            "supplier_name",
            "total_payable",
            "date_last_paid",
            "total_paid",
            "projects_name",
            "status_note",
        ]
        labels = {
            "date_last_paid": "Paid date",
        }
        widgets = {
            "supplier_name": forms.TextInput(attrs={"class": "form-control"}),
            "total_payable": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "total_paid": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "date_last_paid": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "projects_name": forms.TextInput(attrs={"class": "form-control"}),
            "status_note": forms.TextInput(attrs={"class": "form-control"}),
        }
