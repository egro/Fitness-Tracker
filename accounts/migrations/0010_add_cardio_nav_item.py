from django.db import migrations, models

CARDIO_NAV = ("tracker:cardio_list", "Cardio")


def add_cardio_nav(apps, schema_editor):
    User = apps.get_model("auth", "User")
    NavItem = apps.get_model("accounts", "NavItem")
    for user in User.objects.iterator():
        exists = NavItem.objects.filter(user=user, url_name="tracker:cardio_list").exists()
        if not exists:
            max_order = NavItem.objects.filter(user=user, is_system=False).aggregate(
                m=models.Max("order")
            )["m"]
            next_order = (max_order or 0) + 1
            NavItem.objects.create(
                user=user,
                url_name=CARDIO_NAV[0],
                label=CARDIO_NAV[1],
                order=next_order,
                is_visible=True,
                is_system=False,
            )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0009_alter_profile_theme"),
    ]

    operations = [
        migrations.RunPython(add_cardio_nav, migrations.RunPython.noop),
    ]
