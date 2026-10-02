import pyotp
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.db.models.functions import Lower, Now

from .crypto import encrypt

OUTSIDE_ROOM_NAME = "Outside"
SYSTEM_ACCOUNT_EMAIL = "system@invalid"


class Role(models.TextChoices):
    GUEST = "GUEST", "Guest"
    EMPLOYEE = "EMPLOYEE", "Employee"
    ADMIN = "ADMIN", "Administrator"


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

    objects = AccountManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

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

    def __str__(self):
        return f"Account {self.user_id} ({self.role})"
