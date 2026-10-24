import json

import pyotp
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from audit.utils import log_event

from .crypto import decrypt, encrypt
from .models import SYSTEM_ACCOUNT_EMAIL, Account, Role
from .profile import ProfileError, clean_full_name, clean_phone
from .services import AccountError, pseudonymize_account
from .views import role_required

from audit.ratelimit import over_query_limit

PAGE_SIZE = 25


def _json_body(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _page_number(request):
    try:
        page = int(request.GET.get("page", "1"))
    except ValueError:
        return 1
    return max(page, 1)


def _summary(account):
    return {
        "user_id": account.user_id,
        "email": account.email,
        "role": account.role,
        "room": account.room.name,
        "created": account.created.isoformat(),
        "is_active": account.is_active,
        "mfa_enrolled": account.mfa_enrolled,
    }


def _editable_account(request, user_id):
    account = Account.objects.select_related("room").filter(pk=user_id).first()
    if account is None or account.email == SYSTEM_ACCOUNT_EMAIL:
        return None, JsonResponse({"error": "Account not found."}, status=404)
    if account.deleted is not None:
        return None, JsonResponse({"error": "Deleted accounts cannot be modified."}, status=400)
    return account, None


@require_GET
@role_required("ADMIN")
def list_accounts_view(request):
    if over_query_limit(request):
        return JsonResponse({"error": "Too many queries. Try again in a minute."}, status=429)
    accounts = Account.objects.select_related("room").exclude(email=SYSTEM_ACCOUNT_EMAIL)

    role = request.GET.get("role", "")
    if role:
        if role not in Role.values:
            return JsonResponse({"error": "Unknown role."}, status=400)
        accounts = accounts.filter(role=role)

    email = request.GET.get("email", "").strip()[:254]
    if email:
        accounts = accounts.filter(email__icontains=email)

    if request.GET.get("include_deleted") != "1":
        accounts = accounts.filter(deleted__isnull=True)

    page = _page_number(request)
    total = accounts.count()
    rows = accounts.order_by("user_id")[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]

    log_event(request, "DATA_QUERY", user=request.user,
              details=f"table=accounts; role={role or 'any'}; email_filter={'yes' if email else 'no'}; page={page}")
    return JsonResponse(
        {"accounts": [_summary(a) for a in rows], "page": page, "page_size": PAGE_SIZE, "total": total},
        status=200,
    )


@require_GET
@role_required("ADMIN")
def account_detail_view(request, user_id):
    account = Account.objects.select_related("room").filter(pk=user_id).exclude(email=SYSTEM_ACCOUNT_EMAIL).first()
    if account is None:
        return JsonResponse({"error": "Account not found."}, status=404)

    log_event(request, "PERSONAL_DATA_VIEWED", user=request.user, details=f"target account={account.pk}")
    return JsonResponse(
        {**_summary(account), "full_name": decrypt(account.full_name), "phone": decrypt(account.phone)},
        status=200,
    )


@require_POST
@role_required("ADMIN")
def create_account_view(request):
    data = _json_body(request)
    if data is None:
        return JsonResponse({"error": "Invalid request."}, status=400)

    email, password, role = data.get("email"), data.get("password"), data.get("role")
    if not isinstance(email, str) or not isinstance(password, str) or not email or not password:
        return JsonResponse({"error": "Email and password are required."}, status=400)
    if role not in (Role.EMPLOYEE, Role.ADMIN):
        return JsonResponse({"error": "Role must be EMPLOYEE or ADMIN."}, status=400)

    email = email.strip().lower()
    try:
        if len(email) > 254:
            raise ValidationError("Enter a valid email address.")
        validate_email(email)
        validate_password(password, user=Account(email=email))
    except ValidationError as exc:
        return JsonResponse({"error": " ".join(exc.messages)}, status=400)

    try:
        account = Account.objects.create_user(email, password, role=role)
    except IntegrityError:
        return JsonResponse({"error": "An account with that email already exists."}, status=400)

    log_event(request, "PRIVILEGED_ACCOUNT_CREATED", user=account,
              details=f"by admin={request.user.pk}; role={role}")
    return JsonResponse({"message": "Account created. MFA setup is required at first sign-in.",
                         **_summary(account)}, status=201)


@require_POST
@role_required("ADMIN")
def update_account_view(request, user_id):
    account, error = _editable_account(request, user_id)
    if error:
        return error
    data = _json_body(request)
    if data is None:
        return JsonResponse({"error": "Invalid request."}, status=400)

    changed = []
    if "role" in data:
        if data["role"] not in Role.values:
            return JsonResponse({"error": "Unknown role."}, status=400)
        if account.pk == request.user.pk and data["role"] != Role.ADMIN:
            return JsonResponse({"error": "You cannot change your own role."}, status=400)
        if data["role"] != account.role:
            old_role = account.role
            account.role = data["role"]
            changed.append("role")
    try:
        if "full_name" in data:
            account.full_name = encrypt(clean_full_name(data["full_name"]))
            changed.append("full_name")
        if "phone" in data:
            account.phone = encrypt(clean_phone(data["phone"]))
            changed.append("phone")
    except ProfileError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    if changed:
        account.save(update_fields=changed)
        details = f"by admin={request.user.pk}; fields={','.join(changed)}"
        if "role" in changed:
            details += f"; role {old_role}->{account.role}"
        log_event(request, "ACCOUNT_MODIFIED", user=account, details=details)

    return JsonResponse({**_summary(account), "full_name": decrypt(account.full_name),
                         "phone": decrypt(account.phone)}, status=200)


@require_POST
@role_required("ADMIN")
def reset_mfa_view(request, user_id):
    account, error = _editable_account(request, user_id)
    if error:
        return error

    account.totp_secret = encrypt(pyotp.random_base32())
    account.mfa_enrolled = False
    account.save(update_fields=["totp_secret", "mfa_enrolled"])
    log_event(request, "MFA_RESET", user=account, details=f"by admin={request.user.pk}")
    return JsonResponse({"message": "MFA reset. The user will set it up again at next sign-in."}, status=200)


@require_POST
@role_required("ADMIN")
def delete_account_view(request, user_id):
    account, error = _editable_account(request, user_id)
    if error:
        return error
    if account.pk == request.user.pk:
        return JsonResponse({"error": "You cannot delete your own account here."}, status=400)

    try:
        account = pseudonymize_account(account.pk)
    except AccountError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    log_event(request, "ACCOUNT_DELETED", user=account, details=f"by admin={request.user.pk}")
    return JsonResponse({"message": "Account deleted."}, status=200)