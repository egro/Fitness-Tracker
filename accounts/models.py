from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    UNITS_CHOICES = [("metric", "Metric (kg/cm)"), ("imperial", "Imperial (lbs/in)")]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    units = models.CharField(max_length=10, choices=UNITS_CHOICES, default="metric")
    date_of_birth = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} profile"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
