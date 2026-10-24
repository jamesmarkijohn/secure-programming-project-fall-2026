
from django.test import TestCase, tag
from django.urls import reverse

from accounts.models import Account, Role
from gallery.models import GalleryRoom


class AdminAccountSecurityTests(TestCase):

    def setUp(self):
        GalleryRoom.objects.get_or_create(name="Outside")

        self.guest = Account.objects.create_user(
            email="guest-test@example.com",
            password="GuestTestPassword2026!",
            role=Role.GUEST,
        )

        self.employee = Account.objects.create_user(
            email="employee-test@example.com",
            password="EmployeeTestPassword2026!",
            role=Role.EMPLOYEE,
        )

        self.admin = Account.objects.create_user(
            email="admin-test@example.com",
            password="AdminTestPassword2026!",
            role=Role.ADMIN,
        )

    @tag("security")
    def test_guest_cannot_view_accounts(self):
        self.client.force_login(self.guest)
        response = self.client.get(reverse("admin_accounts"))
        self.assertEqual(response.status_code, 403)

    @tag("security")
    def test_employee_cannot_view_accounts(self):
        self.client.force_login(self.employee)
        response = self.client.get(reverse("admin_accounts"))
        self.assertEqual(response.status_code, 403)

    @tag("functional")
    def test_admin_can_view_accounts(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_accounts"))
        self.assertEqual(response.status_code, 200)

    @tag("security")
    def test_account_query_does_not_expose_secrets(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_accounts"))

        self.assertEqual(response.status_code, 200)

        for account in response.json()["accounts"]:
            self.assertNotIn("password", account)
            self.assertNotIn("totp_secret", account)
            self.assertNotIn("full_name", account)
            self.assertNotIn("phone", account)

class AdminAccountCreationTests(TestCase):

    def setUp(self):
        GalleryRoom.objects.get_or_create(name="Outside")

        self.guest = Account.objects.create_user(
            email="guest-create@example.com",
            password="GuestTestPassword2026!",
            role=Role.GUEST,
        )

        self.employee = Account.objects.create_user(
            email="employee-create@example.com",
            password="EmployeeTestPassword2026!",
            role=Role.EMPLOYEE,
        )

        self.admin = Account.objects.create_user(
            email="admin-create@example.com",
            password="AdminTestPassword2026!",
            role=Role.ADMIN,
        )

        self.url = reverse("admin_create_account")

    @tag("security")
    def test_guest_cannot_create_employee(self):
        self.client.force_login(self.guest)
        response = self.client.post(
            self.url,
            data={
                "email": "newemployee@example.com",
                "password": "SecureTestPassword2026!",
                "role": "EMPLOYEE",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            Account.objects.filter(email="newemployee@example.com").exists()
        )

    @tag("security")
    def test_employee_cannot_create_admin(self):
        self.client.force_login(self.employee)
        response = self.client.post(
            self.url,
            data={
                "email": "newadmin@example.com",
                "password": "SecureTestPassword2026!",
                "role": "ADMIN",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            Account.objects.filter(email="newadmin@example.com").exists()
        )

    @tag("security")
    def test_admin_cannot_create_guest(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            self.url,
            data={
                "email": "newguest@example.com",
                "password": "SecureTestPassword2026!",
                "role": "GUEST",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    @tag("functional")
    def test_admin_can_create_employee(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            self.url,
            data={
                "email": "createdemployee@example.com",
                "password": "SecureTestPassword2026!",
                "role": "EMPLOYEE",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)

        account = Account.objects.get(email="createdemployee@example.com")
        self.assertEqual(account.role, Role.EMPLOYEE)
        self.assertFalse(account.mfa_enrolled)
        self.assertTrue(account.check_password("SecureTestPassword2026!"))
