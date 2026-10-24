"""Security tests for sign-up, sign-in, MFA, sessions, and account deletion."""
import pyotp
from django.test import Client, tag

from accounts.crypto import decrypt
from accounts.models import Account, Role
from accounts.testing import PASSWORD, GalleryTestCase
from gallery.models import MovementEvent
from gallery.services import record_move

LOGIN = "/api/auth/login/"
MFA = "/api/auth/verify-mfa/"


class LoginTests(GalleryTestCase):
    def login(self, client, email, password):
        return self.post_json(client, LOGIN, {"email": email, "password": password})

    def current_code(self, user):
        return pyotp.TOTP(decrypt(Account.objects.get(pk=user.pk).totp_secret)).now()

    @tag("functional")
    def test_full_login_with_mfa(self):
        client = Client()
        response = self.login(client, self.guest.email, PASSWORD)
        self.assertEqual(response.status_code, 200)
        self.assertIn("mfa_setup", response.json())  # first sign-in: enrollment

        response = self.post_json(client, MFA, {"code": self.current_code(self.guest)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(client.get("/api/auth/me/").json()["email"], self.guest.email)

    @tag("security")
    def test_password_alone_does_not_sign_in(self):
        client = Client()
        self.login(client, self.guest.email, PASSWORD)
        self.assertEqual(client.get("/api/auth/me/").status_code, 401)

    @tag("security")
    def test_wrong_mfa_code_rejected(self):
        client = Client()
        self.login(client, self.guest.email, PASSWORD)
        response = self.post_json(client, MFA, {"code": "000000"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(client.get("/api/auth/me/").status_code, 401)

    @tag("security")
    def test_mfa_secret_not_shown_after_enrollment(self):
        Account.objects.filter(pk=self.guest.pk).update(mfa_enrolled=True)
        response = self.login(Client(), self.guest.email, PASSWORD)
        self.assertNotIn("mfa_setup", response.json())

    @tag("security")
    def test_failures_are_indistinguishable(self):
        """Unknown email, wrong password, and a locked account all look the same."""
        unknown = self.login(Client(), "nobody@test.local", "wrong-password")
        wrong = self.login(Client(), self.guest.email, "wrong-password")
        for _ in range(5):
            self.login(Client(), self.employee.email, "wrong-password")
        locked = self.login(Client(), self.employee.email, PASSWORD)

        for response in (unknown, wrong, locked):
            self.assertEqual(response.status_code, 401)
        self.assertEqual(unknown.json(), wrong.json())
        self.assertEqual(wrong.json(), locked.json())

    @tag("security")
    def test_lockout_blocks_correct_password(self):
        for _ in range(5):
            self.login(Client(), self.guest.email, "wrong-password")
        response = self.login(Client(), self.guest.email, PASSWORD)
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("mfa_required", response.json())

    @tag("security")
    def test_login_rate_limit_per_client(self):
        for _ in range(10):
            self.login(Client(), "nobody@test.local", "wrong-password")
        self.assertEqual(self.login(Client(), "nobody@test.local", "wrong-password").status_code, 429)

    @tag("security")
    def test_login_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(self.login(client, self.guest.email, PASSWORD).status_code, 403)

    @tag("security")
    def test_malformed_input_is_rejected_cleanly(self):
        for body in ({"email": 123, "password": "x"}, {"email": ["a"], "password": "x"}, {"email": "a@b.c"}):
            self.assertEqual(self.post_json(Client(), LOGIN, body).status_code, 400)

    @tag("security")
    def test_sql_injection_attempt_is_just_a_failed_login(self):
        response = self.login(Client(), "' OR '1'='1", "x")
        self.assertEqual(response.status_code, 401)


class RegistrationTests(GalleryTestCase):
    URL = "/api/auth/register/"

    @tag("security")
    def test_cannot_register_as_admin(self):
        response = self.post_json(Client(), self.URL, {
            "email": "sneaky@test.local", "password": PASSWORD, "role": "ADMIN"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Account.objects.get(email="sneaky@test.local").role, Role.GUEST)

    @tag("security")
    def test_duplicate_email_is_case_insensitive(self):
        response = self.post_json(Client(), self.URL, {"email": "GUEST@test.local", "password": PASSWORD})
        self.assertEqual(response.status_code, 400)

    @tag("security")
    def test_weak_password_rejected(self):
        response = self.post_json(Client(), self.URL, {"email": "weak@test.local", "password": "password"})
        self.assertEqual(response.status_code, 400)

    @tag("security")
    def test_personal_details_are_encrypted(self):
        self.post_json(Client(), self.URL, {
            "email": "named@test.local", "password": PASSWORD, "full_name": "Ada Lovelace"})
        stored = bytes(Account.objects.get(email="named@test.local").full_name)
        self.assertNotIn(b"Ada", stored)
        self.assertEqual(decrypt(stored), "Ada Lovelace")


class SessionTests(GalleryTestCase):
    def assert_signed_out(self, client):
        self.assertEqual(client.get("/api/auth/me/").status_code, 401)

    @tag("security")
    def test_role_change_ends_sessions(self):
        client = self.client_for(self.guest)
        Account.objects.filter(pk=self.guest.pk).update(role=Role.EMPLOYEE)
        self.assert_signed_out(client)

    @tag("security")
    def test_password_change_ends_sessions(self):
        client = self.client_for(self.guest)
        user = Account.objects.get(pk=self.guest.pk)
        user.set_password("a-different-passphrase-2026")
        user.save()
        self.assert_signed_out(client)

    @tag("functional")
    def test_unrelated_change_keeps_session(self):
        client = self.client_for(self.guest)
        Account.objects.filter(pk=self.guest.pk).update(mfa_enrolled=True)
        self.assertEqual(client.get("/api/auth/me/").status_code, 200)


class AccountDeletionTests(GalleryTestCase):
    URL = "/api/auth/delete-account/"

    @tag("functional")
    def test_guest_deletion_pseudonymizes_and_keeps_history(self):
        record_move(self.guest.pk, self.rooms["Lobby"], self.employee)
        record_move(self.guest.pk, self.rooms["Outside"], self.employee)
        client = self.client_for(self.guest)

        response = self.post_json(client, self.URL, {"password": PASSWORD})
        self.assertEqual(response.status_code, 200)

        account = Account.objects.get(pk=self.guest.pk)
        self.assertEqual(account.email, f"deleted-{account.pk}@invalid")
        self.assertFalse(account.has_usable_password())
        self.assertEqual(MovementEvent.objects.filter(user=account).count(), 2)
        self.assertEqual(client.get("/api/auth/me/").status_code, 401)

    @tag("functional")
    def test_cannot_delete_while_inside_gallery(self):
        record_move(self.guest.pk, self.rooms["Lobby"], self.employee)
        response = self.post_json(self.client_for(self.guest), self.URL, {"password": PASSWORD})
        self.assertEqual(response.status_code, 400)

    @tag("security")
    def test_wrong_password_does_not_delete(self):
        response = self.post_json(self.client_for(self.guest), self.URL, {"password": "wrong"})
        self.assertEqual(response.status_code, 401)
        self.assertIsNone(Account.objects.get(pk=self.guest.pk).deleted)

    @tag("security")
    def test_staff_cannot_self_delete(self):
        response = self.post_json(self.client_for(self.employee), self.URL, {"password": PASSWORD})
        self.assertEqual(response.status_code, 403)


class ProfileTests(GalleryTestCase):
    URL = "/api/auth/profile/"

    @tag("security")
    def test_profile_only_returns_own_details(self):
        self.post_json(self.client_for(self.employee), self.URL, {"full_name": "Staff Member"})
        response = self.client_for(self.guest).get(self.URL)
        self.assertEqual(response.json()["email"], self.guest.email)
        self.assertIsNone(response.json()["full_name"])

    @tag("security")
    def test_invalid_phone_rejected(self):
        response = self.post_json(self.client_for(self.guest), self.URL, {"phone": "12"})
        self.assertEqual(response.status_code, 400)
