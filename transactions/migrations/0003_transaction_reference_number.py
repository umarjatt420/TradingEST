from django.db import migrations, models


def populate_transaction_refs(apps, schema_editor):
    Transaction = apps.get_model("transactions", "Transaction")
    for txn in Transaction.objects.all().order_by("pk"):
        txn.reference_number = f"TXN-{txn.pk:06d}"
        txn.save(update_fields=["reference_number"])


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0002_ledger_choice_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="reference_number",
            field=models.CharField(
                blank=True,
                max_length=64,
                null=True,
                verbose_name="Reference #",
            ),
        ),
        migrations.RunPython(populate_transaction_refs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="transaction",
            name="reference_number",
            field=models.CharField(
                db_index=True,
                max_length=64,
                unique=True,
                verbose_name="Reference #",
            ),
        ),
    ]
