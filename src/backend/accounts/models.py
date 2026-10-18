import pyotp
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.db.models.functions import Lower, Now

from .crypto import encrypt

from django.utils.crypto import salted_hmac

OUTSIDE_ROOM_NAME = "Outside"
SYSTEM_ACCOUNT_EMAIL = "system@invalid"


class Role(models.TextChoices):
    GUEST = "GUEST", "Guest"
    EMPLOYEE = "EMPLOYEE", "Employee"
    ADMIN = "ADMIN", "Administrator"


# AccountManager is responsible for creating accounts in a consistent manner
# Ensures that necessary fields are set and that the email is normalized and lowercased
# Also generates a TOTP secret for two-factor authentication and sets the starting location of the account to the "Outside" room
class AccountManager(BaseUserManager):
    """The only way to create accounts, so every account is created
    the same way: sanitized email, hashed password, TOTP secret, and
    starting location of Outside."""

    def create_user(self, email, password, role=Role.GUEST, **extra_fields):
        if not email:
            raise ValueError("An email address is required")
        from gallery.models import GalleryRoom

        account = self.model(
            email=self.normalize_email(email).lower(),
            role=role,
            room=GalleryRoom.objects.get(name=OUTSIDE_ROOM_NAME),
            totp_secret=encrypt(pyotp.random_base32()),
            **extra_fields,
        )
        account.set_password(password)
        account.save(using=self._db)
        return account


# The Account model represents a user account in the system
# It includes fields for email, full name, phone number, role, room, TOTP secret for MFA, etc.
class Account(AbstractBaseUser):
    user_id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=254, unique=True)
    full_name = models.BinaryField(null=True, blank=True)
    phone = models.BinaryField(null=True, blank=True) 
    created = models.DateTimeField(db_default=Now())
    role = models.CharField(max_length=8, choices=Role.choices, default=Role.GUEST)
    room = models.ForeignKey(
        "gallery.GalleryRoom",
        on_delete=models.PROTECT,
        db_column="room_id",
        related_name="occupants",
    )
    totp_secret = models.BinaryField()
    deleted = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    mfa_enrolled = models.BooleanField(default=False)

    objects = AccountManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    # Defines the database table name and constraints for the Account model
    class Meta:
        db_table = "accounts"
        constraints = [
            models.UniqueConstraint(Lower("email"), name="accounts_email_unique"),
            models.CheckConstraint(
                condition=models.Q(role__in=Role.values),
                name="accounts_role_valid",
            ),
        ]

    @property
    def is_active(self):
        return self.deleted is None

    def _get_session_auth_hash(self, secret=None):
        key_salt = "accounts.Account.session_auth_hash"
        value = f"{self.password}|{self.role}|{bytes(self.totp_secret).hex()}"
        return salted_hmac(key_salt, value, secret=secret, algorithm="sha256").hexdigest()

    def __str__(self):
        return f"Account {self.user_id} ({self.role})"
