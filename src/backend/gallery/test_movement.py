"""Security and correctness tests for movement recording and history queries."""
import threading

from django.db import connection
from django.test import TransactionTestCase, tag

from accounts.crypto import decrypt
from accounts.models import Account, Role
from accounts.testing import GalleryTestCase
from audit.models import SecurityLog
from gallery.models import MovementEvent
from gallery.services import MovementError, record_move

MOVES = "/api/gallery/moves/"
HISTORY = "/api/gallery/movement-history/"


class RecordMoveTests(GalleryTestCase):
    def move(self, user, person, room_name):
        return self.post_json(self.client_for(user), MOVES,
                              {"person_id": person.pk, "room_id": self.rooms[room_name]})

    @tag("functional")
    def test_valid_move_updates_location(self):
        self.assertEqual(self.move(self.employee, self.guest, "Lobby").status_code, 201)
        self.assertEqual(Account.objects.get(pk=self.guest.pk).room.name, "Lobby")

    @tag("security")
    def test_guests_cannot_record_moves(self):
        self.assertEqual(self.move(self.guest, self.guest, "Lobby").status_code, 403)

    @tag("functional")
    def test_rooms_must_be_connected(self):
        response = self.move(self.employee, self.guest, "Sculptures")  # Outside -> Sculptures
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Account.objects.get(pk=self.guest.pk).room.name, "Outside")

    @tag("functional")
    def test_cannot_move_to_current_room(self):
        self.assertEqual(self.move(self.employee, self.guest, "Outside").status_code, 400)

    @tag("security")
    def test_move_is_attributed_to_the_session_user(self):
        """recorded_by comes from the session; a value in the request is ignored."""
        self.post_json(self.client_for(self.employee), MOVES, {
            "person_id": self.guest.pk, "room_id": self.rooms["Lobby"], "recorded_by": self.admin.pk})
        self.assertEqual(MovementEvent.objects.get(user=self.guest).recorded_by_id, self.employee.pk)

    @tag("security")
    def test_ids_must_be_integers(self):
        client = self.client_for(self.employee)
        for body in ({"person_id": True, "room_id": 2}, {"person_id": "1", "room_id": 2},
                     {"person_id": -1, "room_id": 2}):
            self.assertEqual(self.post_json(client, MOVES, body).status_code, 400)

    @tag("security")
    def test_guest_entering_staff_room_is_logged(self):
        record_move(self.guest.pk, self.rooms["Lobby"], self.employee)
        record_move(self.guest.pk, self.rooms["Security Office"], self.employee)
        self.assertTrue(SecurityLog.objects.filter(event_type="RESTRICTED_ROOM_ENTRY", user=self.guest).exists())

    @tag("functional")
    def test_staff_entering_staff_room_is_not_logged(self):
        record_move(self.employee.pk, self.rooms["Lobby"], self.employee)
        record_move(self.employee.pk, self.rooms["Security Office"], self.employee)
        self.assertFalse(SecurityLog.objects.filter(event_type="RESTRICTED_ROOM_ENTRY").exists())

    @tag("security")
    def test_deleted_and_system_accounts_cannot_move(self):
        system = Account.objects.get(email="system@invalid")
        with self.assertRaises(MovementError):
            record_move(system.pk, self.rooms["Lobby"], self.employee)


class MovementHistoryTests(GalleryTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        for room in ("Lobby", "Main Hall", "Lobby"):
            record_move(cls.guest.pk, cls.rooms[room], cls.employee)
        record_move(cls.employee.pk, cls.rooms["Lobby"], cls.employee)

    def query(self, user, params=""):
        return self.client_for(user).get(HISTORY + params)

    @tag("security")
    def test_guests_cannot_query(self):
        self.assertEqual(self.query(self.guest).status_code, 403)

    @tag("functional")
    def test_filter_by_person(self):
        data = self.query(self.employee, f"?person_id={self.guest.pk}").json()
        self.assertEqual(data["total"], 3)
        self.assertTrue(all(e["user_id"] == self.guest.pk for e in data["events"]))

    @tag("functional")
    def test_filter_by_room(self):
        data = self.query(self.employee, f"?room_id={self.rooms['Main Hall']}").json()
        self.assertEqual(data["total"], 2)

    @tag("security")
    def test_invalid_filters_rejected(self):
        for params in ("?person_id=1%20OR%201=1", "?room_id=-3", "?since=yesterday"):
            self.assertEqual(self.query(self.employee, params).status_code, 400, params)

    @tag("security")
    def test_queries_are_logged(self):
        self.query(self.employee, f"?person_id={self.guest.pk}")
        entry = SecurityLog.objects.get(event_type="DATA_QUERY", user=self.employee)
        self.assertIn("table=movement_events", decrypt(entry.event_desc))

    @tag("security")
    def test_query_rate_limit_is_per_account(self):
        client = self.client_for(self.employee)
        for _ in range(10):
            client.get(HISTORY)
        self.assertEqual(client.get(HISTORY).status_code, 429)
        self.assertEqual(self.query(self.admin).status_code, 200)  # a different account is unaffected


class EventDeletionTests(GalleryTestCase):
    def setUp(self):
        record_move(self.guest.pk, self.rooms["Lobby"], self.employee)
        record_move(self.guest.pk, self.rooms["Outside"], self.employee)
        self.event = MovementEvent.objects.filter(user=self.guest).latest("event_id")

    def delete(self, user):
        return self.post_json(self.client_for(user), f"/api/gallery/events/{self.event.pk}/delete/")

    @tag("security")
    def test_employees_cannot_delete_events(self):
        self.assertEqual(self.delete(self.employee).status_code, 403)
        self.assertTrue(MovementEvent.objects.filter(pk=self.event.pk).exists())

    @tag("security")
    def test_admin_delete_is_logged_and_keeps_current_room(self):
        self.assertEqual(self.delete(self.admin).status_code, 200)
        self.assertFalse(MovementEvent.objects.filter(pk=self.event.pk).exists())
        # Deleting the "left the gallery" event doesn't put the person back inside.
        self.assertEqual(Account.objects.get(pk=self.guest.pk).room.name, "Outside")
        entry = SecurityLog.objects.get(event_type="MOVEMENT_EVENT_DELETED")
        self.assertIn(f"event={self.event.pk}", decrypt(entry.event_desc))


class MovementRaceTests(TransactionTestCase):
    """Simultaneous identical moves: exactly one may succeed (row locking).

    This needs real commits so the threads can see each other's data, which
    TestCase's rollback doesn't allow.
    """

    def _fixture_teardown(self):
        # Django normally empties every table with TRUNCATE ... CASCADE, which
        # reaches the security log and is refused by its append-only trigger
        # (the trigger working as intended). Remove just this test's rows instead.
        from gallery.models import AdjacentRoom, GalleryRoom
        MovementEvent.objects.all().delete()
        Account.objects.all().delete()
        AdjacentRoom.objects.all().delete()
        GalleryRoom.objects.all().delete()

    @tag("security")
    def test_simultaneous_moves_cannot_both_succeed(self):
        from io import StringIO
        from django.core.management import call_command
        from gallery.models import GalleryRoom

        call_command("load_seed", stdout=StringIO())
        lobby = GalleryRoom.objects.get(name="Lobby").pk
        staff = Account.objects.create_user("staff@race.local", "gallery-test-passphrase-2026", role=Role.EMPLOYEE)
        person = Account.objects.create_user("person@race.local", "gallery-test-passphrase-2026")

        results, barrier = [], threading.Barrier(10)

        def attempt():
            barrier.wait()
            try:
                record_move(person.pk, lobby, staff)
                results.append("ok")
            except MovementError:
                results.append("rejected")
            finally:
                connection.close()

        threads = [threading.Thread(target=attempt) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(results.count("ok"), 1)
        self.assertEqual(MovementEvent.objects.filter(user=person).count(), 1)
