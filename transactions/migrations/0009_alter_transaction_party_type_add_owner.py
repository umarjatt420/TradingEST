from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0008_transactioncategory"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="party_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("Client", "Client"),
                    ("Supplier", "Supplier"),
                    ("Employee", "Employee"),
                    ("Owner", "Owner"),
                ],
                max_length=64,
                null=True,
            ),
        ),
    ]
