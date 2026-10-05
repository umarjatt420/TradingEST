from decimal import Decimal

from django.db import migrations


def backfill_advance_50_percent(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    for project in Project.objects.filter(
        contract_value_excl_vat__isnull=False,
        advance_amount_incl_vat__isnull=True,
    ):
        contract = project.contract_value_excl_vat
        vat = (contract * Decimal("0.15")).quantize(Decimal("0.01"))
        incl = contract + vat
        project.advance_amount_incl_vat = (incl * Decimal("0.5")).quantize(
            Decimal("0.01")
        )
        project.save(update_fields=["advance_amount_incl_vat"])


def noop_reverse(apps, schema_editor):
  pass


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0005_alter_project_advance_amount_incl_vat"),
    ]

    operations = [
        migrations.RunPython(backfill_advance_50_percent, noop_reverse),
    ]
