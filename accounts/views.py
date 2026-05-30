from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from .forms import RegisterForm, ProfileForm
from .models import NavItem, Profile


@method_decorator(ratelimit(key="ip", rate="10/m", method="POST"), name="dispatch")
class CustomLoginView(LoginView):
    template_name = "accounts/login.html"


@ratelimit(key="ip", rate="5/m", method="POST")
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("accounts:profile")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user.profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Settings saved!")
            return redirect("tracker:dashboard")
    else:
        form = ProfileForm(instance=request.user.profile, user=request.user)
    return render(request, "accounts/profile.html", {
        "form": form,
        "nav_color_presets": Profile.NAV_COLOR_PRESETS,
        "nav_color_choices": Profile.NAV_COLOR_CHOICES,
    })


@login_required
def nav_items(request):
    items = NavItem.objects.filter(user=request.user)

    if request.method == "POST":
        action = request.POST.get("action")
        item_id = request.POST.get("item_id")

        if action == "toggle" and item_id:
            item = get_object_or_404(NavItem, pk=item_id, user=request.user)
            if not item.is_system:
                item.is_visible = not item.is_visible
                item.save()
                messages.success(request, f"'{item.label}' {'shown' if item.is_visible else 'hidden'}")

        elif action == "move_up" and item_id:
            item = get_object_or_404(NavItem, pk=item_id, user=request.user)
            prev = NavItem.objects.filter(user=request.user, order__lt=item.order).order_by("-order").first()
            if prev:
                prev.order, item.order = item.order, prev.order
                prev.save()
                item.save()

        elif action == "move_down" and item_id:
            item = get_object_or_404(NavItem, pk=item_id, user=request.user)
            next_item = NavItem.objects.filter(user=request.user, order__gt=item.order).order_by("order").first()
            if next_item:
                next_item.order, item.order = item.order, next_item.order
                next_item.save()
                item.save()

        elif action == "reset":
            request.user.nav_items.all().delete()
            from .models import create_default_nav_items
            create_default_nav_items(request.user)
            messages.success(request, "Navigation reset to defaults!")

        return redirect("accounts:nav_items")

    return render(request, "accounts/nav_items.html", {"items": items})
