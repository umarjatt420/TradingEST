from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0003_project_optional_advance"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="project",
            name="advance_percent",
        ),
    ]
