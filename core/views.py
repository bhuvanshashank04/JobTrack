from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
import secrets
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils import timezone
from .models import PasswordResetOTP, Profile
from .forms import (
    RegistrationForm,
    PasswordResetEmailForm,
    OTPVerificationForm,
    SetNewPasswordForm,
    UserProfileForm,
    ProfilePictureForm,
)
def home(request):
    return render(request, "core/home.html")


def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            messages.success(
                request,
                "Your JobTrack account has been created successfully."
            )

            return redirect("home")

    else:
        form = RegistrationForm()

    return render(
        request,
        "registration/register.html",
        {"form": form},
    )
def password_reset_request(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = PasswordResetEmailForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"].strip()

            from django.contrib.auth.models import User

            user = User.objects.filter(
                email__iexact=email
            ).first()

            if user:
                # Invalidate previous unused OTPs.
                PasswordResetOTP.objects.filter(
                    user=user,
                    is_used=False,
                ).update(is_used=True)

                # Generate a secure 6-digit OTP.
                otp = f"{secrets.randbelow(1000000):06d}"

                # OTP expires after 5 minutes.
                expires_at = timezone.now() + timedelta(minutes=5)

                otp_record = PasswordResetOTP.objects.create(
                    user=user,
                    otp_hash=make_password(otp),
                    expires_at=expires_at,
                )

                try:
                    send_mail(
                        subject="JobTrack - Password Reset OTP",
                        message=(
                            f"Hello {user.username},\n\n"
                            f"Your JobTrack password reset OTP is: {otp}\n\n"
                            "This OTP is valid for 5 minutes.\n"
                            "Do not share this OTP with anyone.\n\n"
                            "If you did not request a password reset, "
                            "please ignore this email."
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=False,
                    )

                    request.session["password_reset_user_id"] = user.id
                    request.session["password_reset_otp_id"] = otp_record.id

                except Exception:
                    otp_record.delete()

                    messages.error(
                        request,
                        "Unable to send the verification email. Please try again."
                    )

                    return redirect("password_reset")

            # Use the same response for registered and unregistered addresses.
            return redirect("password_reset_verify")

    else:
        form = PasswordResetEmailForm()

    return render(
        request,
        "registration/password_reset_form.html",
        {"form": form},
    )
def password_reset_verify(request):

    if request.user.is_authenticated:
        return redirect("home")

    otp_id = request.session.get("password_reset_otp_id")
    user_id = request.session.get("password_reset_user_id")

    if not otp_id or not user_id:
        messages.error(
            request,
            "Your password reset session is invalid. Please request a new OTP."
        )
        return redirect("password_reset")

    otp_record = PasswordResetOTP.objects.filter(
        pk=otp_id,
        user_id=user_id,
        is_used=False,
    ).first()

    if not otp_record:
        messages.error(
            request,
            "Invalid or expired OTP. Please request a new one."
        )
        return redirect("password_reset")

    if timezone.now() >= otp_record.expires_at:
        otp_record.is_used = True
        otp_record.save(update_fields=["is_used"])

        messages.error(
            request,
            "Your OTP has expired. Please request a new one."
        )
        return redirect("password_reset")

    if otp_record.attempts >= 5:
        otp_record.is_used = True
        otp_record.save(update_fields=["is_used"])

        messages.error(
            request,
            "Too many incorrect attempts. Please request a new OTP."
        )
        return redirect("password_reset")

    if request.method == "POST":
        form = OTPVerificationForm(request.POST)

        if form.is_valid():

            otp_record.attempts += 1
            otp_record.save(update_fields=["attempts"])

            if check_password(
                form.cleaned_data["otp"],
                otp_record.otp_hash,
            ):

                otp_record.is_used = True
                otp_record.save(update_fields=["is_used"])

                request.session["password_reset_verified"] = True
                request.session["password_reset_verified_at"] = timezone.now().timestamp()

                return redirect("password_reset_new_password")

            if otp_record.attempts >= 5:
                otp_record.is_used = True
                otp_record.save(update_fields=["is_used"])

                messages.error(
                    request,
                    "Too many incorrect attempts. Please request a new OTP."
                )
                return redirect("password_reset")

            form.add_error("otp", "Incorrect OTP. Please try again.")

    else:
        form = OTPVerificationForm()

    return render(
        request,
        "registration/password_reset_verify.html",
        {"form": form},
    )
def password_reset_new_password(request):

    if request.user.is_authenticated:
        return redirect("home")

    otp_id = request.session.get("password_reset_otp_id")
    user_id = request.session.get("password_reset_user_id")
    verified = request.session.get("password_reset_verified")

    if not otp_id or not user_id or not verified:
        messages.error(
            request,
            "Please verify your OTP before resetting your password."
        )
        return redirect("password_reset")

    otp_record = PasswordResetOTP.objects.filter(
        pk=otp_id,
        user_id=user_id,
        is_used=True,
    ).first()

    if not otp_record:
        messages.error(
            request,
            "Your password reset session is invalid. Please request a new OTP."
        )
        return redirect("password_reset")

    if request.method == "POST":
        form = SetNewPasswordForm(request.POST)

        if form.is_valid():
            from django.contrib.auth.models import User

            user = User.objects.filter(pk=user_id).first()

            if not user:
                messages.error(request, "User account not found.")
                return redirect("password_reset")

            new_password = form.cleaned_data["new_password1"]

            try:
                validate_password(new_password, user=user)
            except ValidationError as error:
                form.add_error("new_password1", error)

            if not form.errors:
                user.set_password(new_password)
                user.save(update_fields=["password"])

                # Invalidate all other outstanding reset OTPs.
                PasswordResetOTP.objects.filter(
                    user=user,
                    is_used=False,
                ).update(is_used=True)

                # Clear password reset session information.
                for key in [
                    "password_reset_otp_id",
                    "password_reset_user_id",
                    "password_reset_verified",
                    "password_reset_verified_at",
                ]:
                    request.session.pop(key, None)

                messages.success(
                    request,
                    "Your password has been reset successfully. Please log in."
                )

                return redirect("login")

    else:
        form = SetNewPasswordForm()

    return render(
        request,
        "registration/password_reset_new_password.html",
        {"form": form},
    )
from django.contrib.auth.decorators import login_required


@login_required
def profile(request):
    user_profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    return render(
        request,
        "registration/profile.html",
        {
            "profile_user": request.user,
            "user_profile": user_profile,
        },
    )


@login_required
def edit_profile(request):
    user_profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":
        user_form = UserProfileForm(
            request.POST,
            instance=request.user,
        )

        picture_form = ProfilePictureForm(
            request.POST,
            request.FILES,
            instance=user_profile,
        )

        if user_form.is_valid() and picture_form.is_valid():
            user_form.save()
            picture_form.save()

            messages.success(
                request,
                "Your profile has been updated successfully."
            )

            return redirect("profile")

    else:
        user_form = UserProfileForm(instance=request.user)
        picture_form = ProfilePictureForm(instance=user_profile)

    return render(
        request,
        "registration/edit_profile.html",
        {
            "user_form": user_form,
            "picture_form": picture_form,
        },
    )