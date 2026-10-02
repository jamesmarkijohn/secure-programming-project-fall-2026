import pyotp
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.db.models.functions import Lower, Now

from .crypto import encrypt

OUTSIDE_ROOM_NAME = "Outside"           # created by database/seed.sql
SYSTEM_ACCOUNT_EMAIL = "system@invalid"  # created by the seed_system_account command


class Role(models.TextChoices):
    GUEST = "GUEST", "Guest"
    EMPLOYEE = "EMPLOYEE", "Employee"
    ADMIN = "ADMIN", "Administrator"


class AccountManager(BaseUserManager):
    """The one sanctioned way to create accounts, so every account is created
    the same way: normalized email, hashed password, fresh TOTP secret, and
    starting location Outside."""

    def create_user(self, email, password, role=Role.GUEST, **extra_fields):
        if not email:
            raise ValueError("An email address is required")
        # Imported here to avoid a circular import between the two apps.
        from gallery.models import GalleryRoom

        account = self.model(
            email=self.normalize_email(email).lower(),
            role=role,
            room=GalleryRoom.objects.get(name=OUTSIDE_ROOM_NAME),
            # The secret must exist from the start (the column is NOT NULL).
            # The user scans it into their authenticator app during enrollment.
            totp_secret=encrypt(pyotp.random_base32()),
            **extra_fields,
        )
        account.set_password(password)  # Argon2id via PASSWORD_HASHERS
        account.save(using=self._db)
        return account


class Account(AbstractBaseUser):
    """Matches the Account entity in the ERD.

    AbstractBaseUser contributes `password` (the hash) and `last_login`, the
    minimum Django's authentication system needs. PermissionsMixin is not used:
    the `role` field is the only source of authorization decisions.
    """

    user_id = models.AutoField(primary_key=True)
    # unique=True is required by Django for the login field; the Lower()
    # constraint below adds case-insensitivity on top of it.
    email = models.EmailField(max_length=254, unique=True)
    # password: inherited from AbstractBaseUser, varchar(128)
    full_name = models.BinaryField(null=True, blank=True)   # encrypted
    phone = models.BinaryField(null=True, blank=True)       # encrypted
    created = models.DateTimeField(db_default=Now())
    role = models.CharField(max_length=8, choices=Role.choices, default=Role.GUEST)
    room = models.ForeignKey(
        "gallery.GalleryRoom",
        on_delete=models.PROTECT,
        db_column="room_id",
        related_name="occupants",
    )
    totp_secret = models.BinaryField()                       # encrypted, NOT NULL
    deleted = models.DateTimeField(null=True, blank=True)    # set on pseudonymization

    objects = AccountManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "accounts"
        constraints = [
            # Case-insensitive: James@x.com and james@x.com can't both exist.
            models.UniqueConstraint(Lower("email"), name="accounts_email_unique"),
            models.CheckConstraint(
                condition=models.Q(role__in=Role.values),
                name="accounts_role_valid",
            ),
        ]

    @property
    def is_active(self):
        # Django's login machinery refuses inactive accounts. A pseudonymized
        # (deleted) account must never authenticate again.
        return self.deleted is None

    def __str__(self):
        return f"Account {self.user_id} ({self.role})"
