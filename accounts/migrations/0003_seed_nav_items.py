from django.db import migrations

DEFAULT_NAV_ITEMS = [
    ("tracker:dashboard", "Dashboard"),
    ("tracker:weight_add", "Log Weight"),
    ("tracker:measurement_add", "Measure"),
    ("tracker:exercise_list", "Exercises"),
    ("tracker:template_list", "Templates"),
    ("tracker:workout_add", "Workout"),
    ("photos:gallery", "Photos"),
]

SYSTEM_NAV_ITEMS = [
    ("accounts:profile", "Settings"),
    ("accounts:logout", "Logout"),
]


def seed_nav_items(apps, schema_editor):
    User = apps.get_model("auth", "User")
    NavItem = apps.get_model("accounts", "NavItem")
    for user in User.objects.iterator():
        for i, (url_name, label) in enumerate(DEFAULT_NAV_ITEMS):
            NavItem.objects.get_or_create(
                user=user, url_name=url_name,
                defaults={"label": label, "order": i, "is_visible": True},
            )
        offset = len(DEFAULT_NAV_ITEMS)
        for i, (url_name, label) in enumerate(SYSTEM_NAV_ITEMS):
            NavItem.objects.get_or_create(
                user=user, url_name=url_name,
                defaults={
                    "label": label, "order": offset + i,
                    "is_visible": True, "is_system": True,
                },
            )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_navitem"),
    ]

    operations = [
        migrations.RunPython(seed_nav_items, migrations.RunPython.noop),
    ]
