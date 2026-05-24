from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ProgressPhoto


@login_required
def upload(request):
    if request.method == "POST":
        images = request.FILES.getlist("images")
        photo_date = request.POST.get("date", date.today())
        body_part = request.POST.get("body_part", "front")
        notes = request.POST.get("notes", "")
        if images:
            for img in images:
                ProgressPhoto.objects.create(
                    user=request.user,
                    date=photo_date,
                    image=img,
                    body_part=body_part,
                    notes=notes,
                )
            messages.success(request, f"{len(images)} photo(s) uploaded!")
            return redirect("photos:gallery")
    return render(request, "photos/upload.html", {
        "today": date.today(),
        "max_date": date.today(),
    })


@login_required
def gallery(request):
    photos = ProgressPhoto.objects.filter(user=request.user).order_by("-date", "-uploaded_at")
    return render(request, "photos/gallery.html", {"photos": photos})


@login_required
def photo_delete(request, pk):
    photo = get_object_or_404(ProgressPhoto, pk=pk, user=request.user)
    photo.image.delete()
    photo.delete()
    messages.success(request, "Photo deleted.")
    return redirect("photos:gallery")
