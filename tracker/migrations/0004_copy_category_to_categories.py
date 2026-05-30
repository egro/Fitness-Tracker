from django.db import migrations


def copy_category_to_categories(apps, schema_editor):
    Exercise = apps.get_model("tracker", "Exercise")
    for ex in Exercise.objects.filter(category__isnull=False).iterator():
        ex.categories.add(ex.category)


class Migration(migrations.Migration):

    dependencies = [
        ("tracker", "0003_add_categories_m2m"),
    ]

    operations = [
        migrations.RunPython(copy_category_to_categories, migrations.RunPython.noop),
    ]
