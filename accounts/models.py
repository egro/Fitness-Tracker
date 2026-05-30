from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    THEME_CHOICES = [
        ("light", "Light"),
        ("dark", "Dark"),
        ("auto", "Auto (follow system)"),
    ]
    NAV_COLOR_CHOICES = [
        ("blue", "Blue"),
        ("slate", "Slate"),
        ("emerald", "Emerald"),
        ("violet", "Violet"),
        ("amber", "Amber"),
        ("rose", "Rose"),
        ("cyan", "Cyan"),
        ("stone", "Stone"),
    ]
    NAV_COLOR_PRESETS = {
        "blue": "#2563eb",
        "slate": "#475569",
        "emerald": "#059669",
        "violet": "#7c3aed",
        "amber": "#d97706",
        "rose": "#e11d48",
        "cyan": "#0891b2",
        "stone": "#57534e",
    }

    UNITS_CHOICES = [
        ("metric", "Metric (kg/cm)"),
        ("imperial", "Imperial (lbs/in)"),
    ]

    SEX_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    date_of_birth = models.DateField(blank=True, null=True)
    height_cm = models.FloatField(blank=True, null=True, verbose_name="Height (cm)")
    goal_weight_kg = models.FloatField(blank=True, null=True, verbose_name="Goal Weight (kg)")
    goal_body_fat_pct = models.FloatField(blank=True, null=True, verbose_name="Goal Body Fat (%)")
    sex = models.CharField(max_length=6, choices=SEX_CHOICES, default="male")
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default="light")
    nav_color = models.CharField(max_length=10, choices=NAV_COLOR_CHOICES, default="blue")
    units = models.CharField(max_length=10, choices=UNITS_CHOICES, default="imperial")

    @property
    def nav_color_hex(self):
        return self.NAV_COLOR_PRESETS.get(self.nav_color, "#2563eb")

    def __str__(self):
        return f"{self.user.username} profile"


DEFAULT_NAV_ITEMS = [
    ("tracker:weight_add", "Log Weight"),
    ("tracker:measurement_add", "Measurements"),
    ("tracker:cardio_list", "Cardio"),
    ("tracker:body_fat_list", "Body Fat"),
    ("tracker:exercise_list", "Exercises"),
    ("tracker:muscle_list", "Muscles"),
    ("tracker:template_list", "Templates"),
    ("tracker:workout_add", "Workout"),
    ("photos:gallery", "Photos"),
    ("tracker:import_export", "Import/Export"),
]

SYSTEM_NAV_ITEMS = [
    ("accounts:profile", "Settings"),
    ("accounts:logout", "Logout"),
]


class NavItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="nav_items")
    label = models.CharField(max_length=100)
    url_name = models.CharField(max_length=200, blank=True)
    url = models.CharField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.user.username} - {self.label}"


def create_default_nav_items(user):
    for i, (url_name, label) in enumerate(DEFAULT_NAV_ITEMS):
        NavItem.objects.get_or_create(
            user=user, url_name=url_name,
            defaults={"label": label, "order": i, "is_visible": True},
        )
    for i, (url_name, label) in enumerate(SYSTEM_NAV_ITEMS):
        offset = len(DEFAULT_NAV_ITEMS)
        NavItem.objects.get_or_create(
            user=user, url_name=url_name,
            defaults={"label": label, "order": offset + i, "is_visible": True, "is_system": True},
        )


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        create_default_nav_items(instance)
