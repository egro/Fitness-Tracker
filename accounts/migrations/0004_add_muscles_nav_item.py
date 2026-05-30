from django.db import migrations


def add_muscles_nav_item(apps, schema_editor):
    NavItem = apps.get_model("accounts", "NavItem")
    for user_id in NavItem.objects.values_list("user", flat=True).distinct():
        has_muscles = NavItem.objects.filter(
            user_id=user_id, url_name="tracker:muscle_list"
        ).exists()
        if not has_muscles:
            shift = NavItem.objects.filter(
                user_id=user_id, order__gte=4
            ).order_by("-order")
            for item in shift:
                item.order += 1
                item.save()
            NavItem.objects.create(
                user_id=user_id,
                url_name="tracker:muscle_list",
                label="Muscles",
                order=4,
                is_visible=True,
            )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_seed_nav_items"),
    ]

    operations = [
        migrations.RunPython(add_muscles_nav_item, migrations.RunPython.noop),
    ]
