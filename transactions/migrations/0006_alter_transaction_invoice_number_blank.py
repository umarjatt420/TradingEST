from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0005_transaction_invoice_number_required"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="invoice_number",
            field=models.CharField(blank=True, max_length=128),
        ),
    ]
