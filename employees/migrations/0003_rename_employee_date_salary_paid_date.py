from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("employees", "0002_employee_date"),
    ]

    operations = [
        migrations.RenameField(
            model_name="employee",
            old_name="date",
            new_name="salary_paid_date",
        ),
        migrations.AlterField(
            model_name="employee",
            name="salary_paid_date",
            field=models.DateField(
                blank=True,
                help_text="Date when salary was paid to this employee.",
                null=True,
                verbose_name="Payment date",
            ),
        ),
    ]
