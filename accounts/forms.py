from datetime import date
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator
from .models import Profile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "mt-1 block w-full rounded border-gray-300 border px-3 py-2"}),
            "email": forms.EmailInput(attrs={"class": "mt-1 block w-full rounded border-gray-300 border px-3 py-2"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "mt-1 block w-full rounded border-gray-300 border px-3 py-2")
        self.fields["password1"].help_text = "At least 8 characters. Cannot be too similar to your personal info or a commonly used password."


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["date_of_birth", "height_cm", "goal_weight_kg", "sex", "theme", "nav_color"]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={
                "type": "date",
                "class": "mt-1 block w-full rounded border-gray-300 border px-3 py-2",
            }),
            "sex": forms.Select(attrs={
                "class": "mt-1 block w-full rounded border-gray-300 border px-3 py-2",
            }),
            "theme": forms.Select(attrs={
                "class": "mt-1 block w-full rounded border-gray-300 border px-3 py-2",
            }),
            "nav_color": forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != "nav_color":
                field.widget.attrs.setdefault("class", "mt-1 block w-full rounded border-gray-300 border px-3 py-2")
        self.fields["date_of_birth"].label = "Date of Birth"
        self.fields["date_of_birth"].validators.append(MaxValueValidator(date.today()))
        self.fields["height_cm"].label = "Height (cm)"
        self.fields["goal_weight_kg"].label = "Goal Weight (kg)"
        self.fields["theme"].label = "Theme"
        self.fields["nav_color"].label = "Nav Bar Color"
