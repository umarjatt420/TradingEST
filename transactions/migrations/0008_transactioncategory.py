from django.db import migrations, models


DEFAULT_CATEGORY_NAMES = [
    "Material Purchase",
    "Project Income",
    "Food Expense",
    "Fuel Expense",
    "Labour Expense",
    "Transport Expense",
    "Owner Drawings",
    "Salary",
]


def seed_transaction_categories(apps, schema_editor):
    TransactionCategory = apps.get_model("transactions", "TransactionCategory")
    Transaction = apps.get_model("transactions", "Transaction")
    names = set(DEFAULT_CATEGORY_NAMES)
    for raw in Transaction.objects.exclude(category="").values_list("category", flat=True).distinct():
        if raw:
            names.add(str(raw).strip())
    for name in sorted(names, key=str.casefold):
        TransactionCategory.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0007_alter_transaction_category_no_choices"),
    ]

    operations = [
        migrations.CreateModel(
            name="TransactionCategory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=128, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name_plural": "Transaction categories",
                "ordering": ["name"],
            },
        ),
        migrations.RunPython(seed_transaction_categories, migrations.RunPython.noop),
    ]
