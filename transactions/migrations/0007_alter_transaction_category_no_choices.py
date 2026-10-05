from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0006_alter_transaction_invoice_number_blank"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="category",
            field=models.CharField(db_index=True, max_length=128),
        ),
    ]
