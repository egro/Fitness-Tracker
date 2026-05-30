from django.db import migrations


def remove_dashboard_nav_item(apps, schema_editor):
    NavItem = apps.get_model("accounts", "NavItem")
    NavItem.objects.filter(url_name="tracker:dashboard").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_add_muscles_nav_item"),
    ]

    operations = [
        migrations.RunPython(remove_dashboard_nav_item, migrations.RunPython.noop),
    ]
