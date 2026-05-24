from django.db import models
from django.contrib.auth.models import User


def photo_path(instance, filename):
    return f"progress_photos/{instance.user.username}/{instance.date}/{filename}"


class ProgressPhoto(models.Model):
    BODY_PARTS = [
        ("front", "Front"),
        ("back", "Back"),
        ("left_side", "Left Side"),
        ("right_side", "Right Side"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="photos")
    date = models.DateField()
    image = models.ImageField(upload_to=photo_path)
    body_part = models.CharField(max_length=20, choices=BODY_PARTS, default="front")
    notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-uploaded_at"]
        verbose_name_plural = "Progress photos"

    def __str__(self):
        return f"{self.user.username} - {self.date} ({self.body_part})"
