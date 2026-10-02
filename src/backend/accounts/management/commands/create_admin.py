"""Interactively creates an administrator account, so no admin credentials
ever need to be stored in seed files or the repository.

Usage: python manage.py create_admin
"""
from getpass import getpass

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from accounts.models import Account, Role


class Command(BaseCommand):
    help = "Create an administrator account (prompts for email and password)."

    def handle(self, *args, **options):
        email = input("Admin email: ").strip()
        if Account.objects.filter(email__iexact=email).exists():
            raise CommandError("An account with that email already exists.")

        password = getpass("Password: ")
        if password != getpass("Password (again): "):
            raise CommandError("Passwords do not match.")
        try:
            validate_password(password)  # same rules as every other account
        except ValidationError as exc:
            raise CommandError(" ".join(exc.messages))

        Account.objects.create_user(email, password, role=Role.ADMIN)
        self.stdout.write(self.style.SUCCESS(f"Administrator {email} created."))
