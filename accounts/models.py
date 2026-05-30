from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    date_of_birth = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} profile"


DEFAULT_NAV_ITEMS = [
    ("tracker:weight_add", "Log Weight"),
    ("tracker:measurement_add", "Measure"),
    ("tracker:exercise_list", "Exercises"),
    ("tracker:muscle_list", "Muscles"),
    ("tracker:template_list", "Templates"),
    ("tracker:workout_add", "Workout"),
    ("photos:gallery", "Photos"),
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
