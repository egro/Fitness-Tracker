from django.db import migrations


def add_importexport_nav_item(apps, schema_editor):
    NavItem = apps.get_model("accounts", "NavItem")
    for user_id in NavItem.objects.values_list("user", flat=True).distinct():
        has_it = NavItem.objects.filter(
            user_id=user_id, url_name="tracker:import_export"
        ).exists()
        if not has_it:
            shift = NavItem.objects.filter(
                user_id=user_id, order__gte=8
            ).order_by("-order")
            for item in shift:
                item.order += 1
                item.save()
            NavItem.objects.create(
                user_id=user_id,
                url_name="tracker:import_export",
                label="Import/Export",
                order=8,
                is_visible=True,
            )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0011_profile_sex"),
    ]

    operations = [
        migrations.RunPython(add_importexport_nav_item, migrations.RunPython.noop),
    ]
