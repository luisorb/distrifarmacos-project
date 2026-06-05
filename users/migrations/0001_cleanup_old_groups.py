from django.db import migrations

def cleanup_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=["digitador", "gestor_calidad", "admin_proyecto"]).delete()

class Migration(migrations.Migration):
    dependencies = []

    operations = [migrations.RunPython(cleanup_groups)]