import pyotp
from django.db import transaction
from django.utils import timezone

from .crypto import encrypt
from .models import OUTSIDE_ROOM_NAME, Account


class AccountError(Exception):
    """An account operation that isn't allowed."""


# Pseudonymize an account by removing personal information and resetting the password and TOTP secret
# This will not invalidate the logs that were related to this account, but it will make it impossible to identify the user from the account data
def pseudonymize_account(account_id):
    with transaction.atomic():
        account = Account.objects.select_for_update().select_related("room").get(pk=account_id)

        if account.deleted is not None:
            raise AccountError("This account has already been deleted.")

        if account.room.name != OUTSIDE_ROOM_NAME:
            raise AccountError("Leave the gallery before deleting the account.")

        account.email = f"deleted-{account.pk}@invalid"
        account.set_unusable_password()
        account.full_name = None
        account.phone = None
        account.totp_secret = encrypt(pyotp.random_base32())
        account.mfa_enrolled = False
        account.failed_login_attempts = 0
        account.locked_until = None
        account.deleted = timezone.now()
        account.save()
        return account