"""Tests that the security log is append-only and read-only through the app."""
from django.test import tag
from django.db import DatabaseError, connection, transaction

from accounts.crypto import encrypt
from accounts.testing import GalleryTestCase
from audit.models import SecurityLog

URL = "/api/audit/security-logs/"


class AppendOnlyTests(GalleryTestCase):
    def setUp(self):
        self.entry = SecurityLog.objects.create(user=self.guest, event_type="TEST", event_desc=encrypt("x"))

    def assert_refused(self, action):
        with self.assertRaises(DatabaseError), transaction.atomic():
            action()

    @tag("security")
    def test_update_refused(self):
        self.assert_refused(lambda: SecurityLog.objects.filter(pk=self.entry.pk).update(event_type="EDITED"))

    @tag("security")
    def test_delete_refused(self):
        self.assert_refused(lambda: SecurityLog.objects.filter(pk=self.entry.pk).delete())

    @tag("security")
    def test_truncate_refused(self):
        def truncate():
            with connection.cursor() as cursor:
                cursor.execute("TRUNCATE security_log")
        self.assert_refused(truncate)

    @tag("security")
    def test_raw_sql_update_refused(self):
        def raw_update():
            with connection.cursor() as cursor:
                cursor.execute("UPDATE security_log SET event_type = 'EDITED'")
        self.assert_refused(raw_update)


class LogViewerTests(GalleryTestCase):
    @tag("security")
    def test_viewer_is_read_only(self):
        client = self.client_for(self.admin)
        self.assertEqual(client.post(URL).status_code, 405)

    @tag("functional")
    def test_filter_by_event_type(self):
        SecurityLog.objects.create(user=self.guest, event_type="TEST_EVENT", event_desc=encrypt("x"))
        data = self.client_for(self.admin).get(URL + "?event_type=TEST_EVENT").json()
        self.assertEqual(data["total"], 1)

    @tag("security")
    def test_invalid_filter_rejected(self):
        response = self.client_for(self.admin).get(URL + "?event_type=x;drop")
        self.assertEqual(response.status_code, 400)

    @tag("security")
    def test_reading_the_log_is_logged(self):
        self.client_for(self.admin).get(URL)
        self.assertTrue(SecurityLog.objects.filter(event_type="DATA_QUERY", user=self.admin).exists())
