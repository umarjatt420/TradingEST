from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0003_transaction_reference_number"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="transaction",
            name="material_item",
        ),
    ]
