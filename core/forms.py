from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegistrationForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your email",
            }
        ),
    )

    class Meta:
        model = User

        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        ]   

        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Choose a username",
                }
            ),
            "first_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter your first name",
            }),

            "last_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter your last name",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in ("password1", "password2"):
            self.fields[field_name].widget.attrs.update({
                "class": "form-control",
            })

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email

class PasswordResetEmailForm(forms.Form):
    email = forms.EmailField(
        label="Registered Email",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your registered email",
            "autocomplete": "email",
        }),
    )


class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        label="6-Digit OTP",
        min_length=6,
        max_length=6,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your 6-digit OTP",
            "autocomplete": "one-time-code",
            "inputmode": "numeric",
        }),
    )

    def clean_otp(self):
        otp = self.cleaned_data["otp"]

        if not otp.isdigit():
            raise forms.ValidationError("OTP must contain exactly 6 digits.")

        return otp


class SetNewPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Enter new password",
        }),
    )

    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Confirm new password",
        }),
    )

    def clean(self):
        cleaned_data = super().clean()

        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The passwords do not match.")

        return cleaned_data
from .models import Profile


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter your first name",
            }),
            "last_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter your last name",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Enter your email address",
            }),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exclude(
            pk=self.instance.pk
        ).exists():
            raise forms.ValidationError(
                "This email address is already being used by another account."
            )

        return email


class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["profile_picture"]
        widgets = {
            "profile_picture": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
            }),
        }