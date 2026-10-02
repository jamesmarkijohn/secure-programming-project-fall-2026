"""Creates the system account that security events with no associated user
are attributed to. Safe to run repeatedly: does nothing if it already exists.

Usage: python manage.py seed_system_account
"""
from django.core.management.base import BaseCommand

from accounts.models import SYSTEM_ACCOUNT_EMAIL, Account


class Command(BaseCommand):
    help = "Create the system account used for security events with no user."

    def handle(self, *args, **options):
        if Account.objects.filter(email=SYSTEM_ACCOUNT_EMAIL).exists():
            self.stdout.write("System account already exists.")
            return
        # password=None makes Django store an *unusable* password: no input
        # will ever match it, so this account can never log in.
        Account.objects.create_user(SYSTEM_ACCOUNT_EMAIL, password=None)
        self.stdout.write(self.style.SUCCESS("System account created."))
