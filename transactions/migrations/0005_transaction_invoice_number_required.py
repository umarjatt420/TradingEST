from django.db import migrations, models


def fill_missing_invoice_numbers(apps, schema_editor):
    Transaction = apps.get_model("transactions", "Transaction")
    for txn in Transaction.objects.filter(invoice_number=""):
        txn.invoice_number = f"INV-{txn.pk:06d}"
        txn.save(update_fields=["invoice_number"])


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0004_remove_transaction_material_item"),
    ]

    operations = [
        migrations.RunPython(fill_missing_invoice_numbers, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="transaction",
            name="invoice_number",
            field=models.CharField(max_length=128),
        ),
    ]
