from django import forms

from .models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "reference_number",
            "name",
            "client_name",
            "contract_value_excl_vat",
            "advance_amount_incl_vat",
            "notes",
        ]
        labels = {
            "reference_number": "Reference #",
            "name": "Project Name",
            "client_name": "Client Name",
            "contract_value_excl_vat": "Contract Value (Excl. VAT)",
            "advance_amount_incl_vat": "Client advance (incl. VAT)",
        }
        help_texts = {
            "advance_amount_incl_vat": (
                "Optional. Amount received from client (incl. VAT). % of contract is calculated automatically."
            ),
        }
        widgets = {
            "reference_number": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "client_name": forms.TextInput(attrs={"class": "form-control"}),
            "contract_value_excl_vat": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "advance_amount_incl_vat": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "e.g. 6000",
                }
            ),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def clean_advance_amount_incl_vat(self):
        amt = self.cleaned_data.get("advance_amount_incl_vat")
        if amt is not None and amt < 0:
            raise forms.ValidationError("Advance cannot be negative.")
        return amt

    def clean(self):
        cleaned = super().clean()
        amt = cleaned.get("advance_amount_incl_vat")
        if amt is not None and cleaned.get("contract_value_excl_vat") is None:
            self.add_error(
                "contract_value_excl_vat",
                "Contract value is required to record client advance.",
            )
        return cleaned

    def clean_reference_number(self):
        ref = (self.cleaned_data.get("reference_number") or "").strip()
        if not ref:
            raise forms.ValidationError("Reference # is required.")
        qs = Project.objects.filter(reference_number__iexact=ref)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This reference # is already in use.")
        return ref
