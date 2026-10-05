"""Transaction field labels — one style everywhere (form, detail, list)."""

TRANSACTION_FIELD_LABELS: dict[str, str] = {
    "project_reference": "Reference #",
    "project": "Project Name",
    "date": "Date",
    "description": "Description",
    "flow_type": "Type (IN/OUT)",
    "amount_excl_vat": "Amount (Excl. VAT)",
    "account": "Account",
    "category": "Category",
    "qty": "Quantity",
    "rate": "Per Unit Price (Excl & Incl)",
    "party_name": "Party Name",
    "party_type": "Party Type",
    "invoice_number": "Invoice #",
    "tax_percent": "Tax %",
    "tax_amount": "Tax Amount",
    "total_amount": "Total Amount",
    "payment_status": "Payment Status",
    "notes": "Notes",
}


def transaction_field_labels() -> dict[str, str]:
    return dict(TRANSACTION_FIELD_LABELS)


def apply_transaction_field_labels(form) -> None:
    """Set form field labels to match TRANSACTION_FIELD_LABELS."""
    for name, label in TRANSACTION_FIELD_LABELS.items():
        if name in form.fields:
            form.fields[name].label = label
