"""Security tests for administrator account management."""
from django.test import tag
from accounts.crypto import decrypt
from accounts.models import SYSTEM_ACCOUNT_EMAIL, Account, Role
from accounts.testing import GalleryTestCase
from audit.models import SecurityLog
from gallery.services import record_move

BASE = "/api/admin/accounts"


class AdminAccessTests(GalleryTestCase):
    """Every admin endpoint must refuse guests and employees, whatever the request."""

    @tag("security")
    def test_non_admins_are_refused_everywhere(self):
        target = self.make_user("target@test.local")
        for user in (self.guest, self.employee):
            client = self.client_for(user)
            self.assertEqual(client.get(f"{BASE}/").status_code, 403)
            self.assertEqual(client.get(f"{BASE}/{target.pk}/").status_code, 403)
            for action in ("update", "reset-mfa", "delete"):
                response = self.post_json(client, f"{BASE}/{target.pk}/{action}/", {"role": "ADMIN"})
                self.assertEqual(response.status_code, 403, f"{user.role} {action}")
        self.assertEqual(Account.objects.get(pk=target.pk).role, Role.GUEST)

    @tag("security")
    def test_signed_out_requests_are_refused(self):
        from django.test import Client
        self.assertEqual(Client().get(f"{BASE}/").status_code, 401)


class AdminAccountManagementTests(GalleryTestCase):
    def setUp(self):
        self.client = self.client_for(self.admin)
        self.target = self.make_user("target@test.local")

    def update(self, user_id, data):
        return self.post_json(self.client, f"{BASE}/{user_id}/update/", data)

    @tag("security")
    def test_role_change_is_logged_with_acting_admin(self):
        self.assertEqual(self.update(self.target.pk, {"role": "EMPLOYEE"}).status_code, 200)
        entry = SecurityLog.objects.get(event_type="ACCOUNT_MODIFIED", user=self.target)
        details = decrypt(entry.event_desc)
        self.assertIn(f"by admin={self.admin.pk}", details)
        self.assertIn("GUEST->EMPLOYEE", details)

    @tag("security")
    def test_role_change_signs_target_out(self):
        target_client = self.client_for(self.target)
        self.update(self.target.pk, {"role": "EMPLOYEE"})
        self.assertEqual(target_client.get("/api/auth/me/").status_code, 401)

    @tag("security")
    def test_invalid_role_rejected(self):
        self.assertEqual(self.update(self.target.pk, {"role": "ROOT"}).status_code, 400)

    @tag("security")
    def test_admin_cannot_demote_self(self):
        self.assertEqual(self.update(self.admin.pk, {"role": "GUEST"}).status_code, 400)
        self.assertEqual(Account.objects.get(pk=self.admin.pk).role, Role.ADMIN)

    @tag("security")
    def test_admin_cannot_delete_self(self):
        response = self.post_json(self.client, f"{BASE}/{self.admin.pk}/delete/")
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(Account.objects.get(pk=self.admin.pk).deleted)

    @tag("security")
    def test_system_account_is_untouchable(self):
        system = Account.objects.get(email=SYSTEM_ACCOUNT_EMAIL)
        self.assertEqual(self.update(system.pk, {"role": "ADMIN"}).status_code, 404)
        self.assertEqual(self.client.get(f"{BASE}/{system.pk}/").status_code, 404)

    @tag("security")
    def test_deleted_account_cannot_be_modified(self):
        self.post_json(self.client, f"{BASE}/{self.target.pk}/delete/")
        self.assertEqual(self.update(self.target.pk, {"role": "ADMIN"}).status_code, 400)

    @tag("functional")
    def test_admin_delete_pseudonymizes(self):
        response = self.post_json(self.client, f"{BASE}/{self.target.pk}/delete/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Account.objects.get(pk=self.target.pk).email, f"deleted-{self.target.pk}@invalid")

    @tag("functional")
    def test_cannot_delete_someone_inside_the_gallery(self):
        record_move(self.target.pk, self.rooms["Lobby"], self.employee)
        response = self.post_json(self.client, f"{BASE}/{self.target.pk}/delete/")
        self.assertEqual(response.status_code, 400)

    @tag("functional")
    def test_reset_mfa_issues_new_secret(self):
        Account.objects.filter(pk=self.target.pk).update(mfa_enrolled=True)
        old_secret = bytes(Account.objects.get(pk=self.target.pk).totp_secret)
        self.post_json(self.client, f"{BASE}/{self.target.pk}/reset-mfa/")
        account = Account.objects.get(pk=self.target.pk)
        self.assertNotEqual(bytes(account.totp_secret), old_secret)
        self.assertFalse(account.mfa_enrolled)

    @tag("security")
    def test_viewing_personal_details_is_logged(self):
        self.client.get(f"{BASE}/{self.target.pk}/")
        entry = SecurityLog.objects.get(event_type="PERSONAL_DATA_VIEWED")
        self.assertIn(f"target account={self.target.pk}", decrypt(entry.event_desc))

    @tag("security")
    def test_invalid_personal_details_rejected(self):
        self.assertEqual(self.update(self.target.pk, {"phone": "12"}).status_code, 400)
        self.assertEqual(self.update(self.target.pk, {"full_name": "x" * 101}).status_code, 400)

    @tag("security")
    def test_list_never_exposes_secrets(self):
        body = self.client.get(f"{BASE}/").content.decode()
        for field in ("password", "totp_secret", "argon2"):
            self.assertNotIn(field, body)
