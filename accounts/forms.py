from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
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


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["date_of_birth"]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
        }
