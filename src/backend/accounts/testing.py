"""Shared setup for tests: the real floor plan, the system account, and one
user per role. Not a test module itself (no `test` prefix), just a base class."""
import json
import logging
from io import StringIO

from django.core.management import call_command
from django.test import Client, TestCase

from accounts.models import Account, Role
from gallery.models import GalleryRoom

PASSWORD = "gallery-test-passphrase-2026"


class GalleryTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Keep test output readable: security events are checked in the database,
        # not printed.
        logging.disable(logging.WARNING)

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)
        super().tearDownClass()

    @classmethod
    def setUpTestData(cls):
        # The same rooms and connections as a real deployment.
        call_command("load_seed", stdout=StringIO())
        call_command("seed_system_account", stdout=StringIO())
        cls.rooms = {room.name: room.pk for room in GalleryRoom.objects.all()}
        cls.guest = cls.make_user("guest@test.local", Role.GUEST)
        cls.employee = cls.make_user("employee@test.local", Role.EMPLOYEE)
        cls.admin = cls.make_user("admin@test.local", Role.ADMIN)

    @staticmethod
    def make_user(email, role=Role.GUEST):
        return Account.objects.create_user(email, PASSWORD, role=role)

    @staticmethod
    def client_for(user):
        client = Client()
        client.force_login(user)
        return client

    @staticmethod
    def post_json(client, url, data=None):
        return client.post(url, json.dumps(data or {}), content_type="application/json")
