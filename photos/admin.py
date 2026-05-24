from django.contrib import admin
from .models import ProgressPhoto


@admin.register(ProgressPhoto)
class ProgressPhotoAdmin(admin.ModelAdmin):
    list_display = ["user", "date", "body_part"]
    list_filter = ["user", "body_part"]
