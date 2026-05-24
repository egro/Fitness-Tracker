from django.urls import path
from . import views

app_name = "photos"

urlpatterns = [
    path("", views.gallery, name="gallery"),
    path("upload/", views.upload, name="upload"),
    path("<int:pk>/delete/", views.photo_delete, name="photo_delete"),
]
