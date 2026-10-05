from django.db import migrations, models


def populate_project_refs(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    for project in Project.objects.all().order_by("pk"):
        project.reference_number = f"PRJ-{project.pk:04d}"
        project.save(update_fields=["reference_number"])


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="reference_number",
            field=models.CharField(
                blank=True,
                max_length=64,
                null=True,
                verbose_name="Reference #",
            ),
        ),
        migrations.RunPython(populate_project_refs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="project",
            name="reference_number",
            field=models.CharField(
                db_index=True,
                max_length=64,
                unique=True,
                verbose_name="Reference #",
            ),
        ),
    ]
