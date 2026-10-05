from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0002_project_reference_number"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="advance_percent",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Optional. e.g. 10, 20, or 50 — leave blank if client pays no advance.",
                max_digits=5,
                null=True,
                verbose_name="Advance %",
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="advance_amount_incl_vat",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Optional fixed amount. Overrides % calculation when set.",
                max_digits=14,
                null=True,
                verbose_name="Advance amount (incl. VAT)",
            ),
        ),
    ]
