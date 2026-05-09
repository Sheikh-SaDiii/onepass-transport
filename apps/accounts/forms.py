from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Role, ProviderProfile, TransportKind


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Email or Username",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "you@example.com"}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "••••••••"}),
    )


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(
        choices=[(Role.USER, "Passenger"), (Role.PROVIDER, "Service Provider")],
        initial=Role.USER,
    )
    phone = forms.CharField(required=False)
    company_name = forms.CharField(required=False, help_text="Required if registering as Provider")
    transport_kind = forms.ChoiceField(
        required=False, choices=[("", "—")] + list(TransportKind.choices)
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "role",
            "company_name",
            "transport_kind",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = field.widget.attrs.get("class", "")
            if isinstance(field.widget, (forms.Select,)):
                field.widget.attrs["class"] = (css + " form-select").strip()
            else:
                field.widget.attrs["class"] = (css + " form-control").strip()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("role") == Role.PROVIDER:
            if not cleaned.get("company_name"):
                self.add_error("company_name", "Company name is required for providers.")
            if not cleaned.get("transport_kind"):
                self.add_error("transport_kind", "Choose the transport type you operate.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.role = self.cleaned_data["role"]
        user.phone = self.cleaned_data.get("phone", "")
        # Providers must wait for admin approval
        user.is_approved = user.role != Role.PROVIDER
        if commit:
            user.save()
            if user.role == Role.PROVIDER:
                ProviderProfile.objects.create(
                    user=user,
                    company_name=self.cleaned_data["company_name"],
                    transport_kind=self.cleaned_data["transport_kind"],
                )
        return user
