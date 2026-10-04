import json
from datetime import timedelta
from functools import wraps

import pyotp

from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .crypto import decrypt
from .models import Account


# Checks if the user is logged in and has the right role
def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse(
                    {"error": "Authentication required."},
                    status=401,
                )

            if request.user.role not in allowed_roles:
                return JsonResponse(
                    {"error": "Permission denied."},
                    status=403,
                )

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


# Gives the frontend a CSRF cookie
@require_GET
@ensure_csrf_cookie
def csrf_view(request):
    return JsonResponse(
        {"message": "CSRF cookie set."},
        status=200,
    )


@require_POST
def login_view(request):
    # Get the email and password from the request
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid request."}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({"error": "Invalid request."}, status=400)

    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or not isinstance(password, str) or not email or not password:
        return JsonResponse(
            {"error": "Email and password are required."},
            status=400,
        )

    # Find the account using the email
    user = Account.objects.filter(email=email.lower()).first()

    if user is None or not user.is_active:
        return JsonResponse(
            {"error": "Invalid email or password."},
            status=401,
        )

    # Check if the account is locked
    if user.locked_until is not None:
        if timezone.now() < user.locked_until:
            return JsonResponse(
                {"error": "Account temporarily locked. Try again later."},
                status=403,
            )

        # Reset the lock after the lock time ends
        user.locked_until = None
        user.failed_login_attempts = 0
        user.save(
            update_fields=["locked_until", "failed_login_attempts"]
        )

    # Check if the password is correct
    if not user.check_password(password):
        user.failed_login_attempts += 1

        # Lock the account for 5 minutes after 5 failed attempts
        if user.failed_login_attempts >= 5:
            user.locked_until = timezone.now() + timedelta(minutes=5)
            user.failed_login_attempts = 0
            user.save(
                update_fields=["failed_login_attempts", "locked_until"]
            )

            return JsonResponse(
                {
                    "error": (
                        "Account temporarily locked. "
                        "Try again later."
                    )
                },
                status=403,
            )

        user.save(update_fields=["failed_login_attempts"])

        return JsonResponse(
            {"error": "Invalid email or password."},
            status=401,
        )

    # Reset failed attempts after the correct password
    if user.failed_login_attempts != 0 or user.locked_until is not None:
        user.failed_login_attempts = 0
        user.locked_until = None
        user.save(
            update_fields=["failed_login_attempts", "locked_until"]
        )

    # Save the user temporarily until MFA is completed
    request.session["pre_mfa_user_id"] = user.pk
    request.session["pre_mfa_authenticated"] = True
    request.session["failed_mfa_attempts"] = 0

    # Give the user 60 seconds to finish MFA
    request.session.set_expiry(60)

    response = {
        "message": "Password verified. MFA required.",
        "mfa_required": True,
    }

    if not user.mfa_enrolled:
        secret = decrypt(user.totp_secret)
        response["mfa_setup"] = {
            "secret": secret,
            "uri": pyotp.TOTP(secret).provisioning_uri(
                name=user.email, issuer_name="Secure Art Gallery"
            ),
        }

    return JsonResponse(response, status=200)



@require_POST
def verify_mfa_view(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid request."}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({"error": "Invalid request."}, status=400)

    code = data.get("code")
    user_id = request.session.get("pre_mfa_user_id")

    if not code or not user_id:
        return JsonResponse(
            {"error": "Invalid or expired MFA request."},
            status=401,
        )

    # Get the account that passed the password step
    try:
        user = Account.objects.get(pk=user_id)
    except Account.DoesNotExist:
        request.session.flush()
        return JsonResponse(
            {"error": "Invalid or expired MFA request."},
            status=401,
        )

    # Check the code from the authenticator app
    secret = decrypt(user.totp_secret)
    totp = pyotp.TOTP(secret)

    if not totp.verify(str(code), valid_window=1):
        failed_mfa_attempts = (
            request.session.get("failed_mfa_attempts", 0) + 1
        )

        # Make the user log in again after 5 wrong MFA codes
        if failed_mfa_attempts >= 5:
            request.session.flush()

            return JsonResponse(
                {
                    "error": (
                        "Too many invalid MFA attempts. "
                        "Please log in again."
                    )
                },
                status=403,
            )

        request.session["failed_mfa_attempts"] = failed_mfa_attempts

        return JsonResponse(
            {"error": "Invalid MFA code."},
            status=401,
        )

    # MFA passed, so the user can now log in
    if not user.mfa_enrolled:
        user.mfa_enrolled = True
        user.save(update_fields=["mfa_enrolled"])
    login(request, user)

    # Change the temporary session to the normal 8 hour session
    request.session.set_expiry(8 * 60 * 60)

    # Remove the temporary MFA information
    request.session.pop("pre_mfa_user_id", None)
    request.session.pop("pre_mfa_authenticated", None)
    request.session.pop("failed_mfa_attempts", None)

    return JsonResponse(
        {
            "message": "Login successful.",
            "role": user.role,
        },
        status=200,
    )


@require_POST
def logout_view(request):
    # Only logged in users can log out
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Authentication required."},
            status=401,
        )

    logout(request)

    return JsonResponse(
        {"message": "Logout successful."},
        status=200,
    )


# Temporary endpoint used to test admin access
@role_required("ADMIN")
def admin_test_view(request):
    return JsonResponse(
        {"message": "Admin access granted."},
        status=200,
    )