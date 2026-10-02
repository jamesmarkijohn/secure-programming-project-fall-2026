"""Runs database/seed.sql against the database. The seed file is written to
be safe to run repeatedly, so this runs on every container start.

Usage: python manage.py load_seed
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

SEED_FILE = Path(settings.BASE_DIR) / "database" / "seed.sql"


class Command(BaseCommand):
    help = "Load gallery rooms and connections from database/seed.sql."

    def handle(self, *args, **options):
        if not SEED_FILE.exists():
            raise CommandError(f"Seed file not found: {SEED_FILE}")
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(SEED_FILE.read_text())
        self.stdout.write(self.style.SUCCESS("Seed data loaded."))
