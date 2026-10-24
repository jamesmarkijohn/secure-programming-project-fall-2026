from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from gallery.models import GalleryRoom

SEED_FILE = Path(settings.BASE_DIR) / "database" / "seed.sql"


class Command(BaseCommand):
    help = "Load gallery rooms and connections from database/seed.sql into a fresh database."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Apply even if rooms already exist.")

    def handle(self, *args, **options):
        if GalleryRoom.objects.exists() and not options["force"]:
            self.stdout.write("Rooms already exist; seed skipped.")
            return
        if not SEED_FILE.exists():
            raise CommandError(f"Seed file not found: {SEED_FILE}")
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(SEED_FILE.read_text())
        self.stdout.write(self.style.SUCCESS("Seed data loaded."))