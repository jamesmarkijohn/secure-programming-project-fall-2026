
from django.test import TestCase, tag
from django.urls import reverse

from accounts.crypto import encrypt
from accounts.models import Account, Role
from audit.models import SecurityLog
from gallery.models import GalleryRoom


class SecurityLogTests(TestCase):

    def setUp(self):
        GalleryRoom.objects.get_or_create(name="Outside")

        self.guest = Account.objects.create_user(
            email="guest-audit@example.com",
            password="GuestTestPassword2026!",
            role=Role.GUEST,
        )

        self.employee = Account.objects.create_user(
            email="employee-audit@example.com",
            password="EmployeeTestPassword2026!",
            role=Role.EMPLOYEE,
        )

        self.admin = Account.objects.create_user(
            email="admin-audit@example.com",
            password="AdminTestPassword2026!",
            role=Role.ADMIN,
        )

        self.url = reverse("security_logs")

    @tag("security")
    def test_guest_cannot_view_security_logs(self):
        self.client.force_login(self.guest)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    @tag("security")
    def test_employee_cannot_view_security_logs(self):
        self.client.force_login(self.employee)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    @tag("functional")
    def test_admin_can_view_security_logs(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    @tag("functional")
    def test_security_log_returns_decrypted_description(self):
        log = SecurityLog.objects.create(
            user=self.employee,
            event_type="TEST_EVENT",
            event_desc=encrypt("Test security event"),
        )

        self.client.force_login(self.admin)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        matching_logs = [
            item for item in response.json()["logs"]
            if item["log_id"] == log.log_id
        ]

        self.assertEqual(len(matching_logs), 1)
        self.assertEqual(
            matching_logs[0]["event_desc"],
            "Test security event",
        )
        self.assertEqual(
            matching_logs[0]["event_type"],
            "TEST_EVENT",
        )
