"""Tests for administrator room management."""
from django.test import tag
from accounts.testing import GalleryTestCase
from audit.models import SecurityLog
from gallery.models import GalleryRoom
from gallery.services import record_move, rooms_are_adjacent

BASE = "/api/admin/rooms"


class AdminRoomTests(GalleryTestCase):
    def setUp(self):
        self.client = self.client_for(self.admin)

    def pair(self, a, b):
        return {"room_a_id": self.rooms[a], "room_b_id": self.rooms[b]}

    @tag("security")
    def test_employees_cannot_manage_rooms(self):
        client = self.client_for(self.employee)
        self.assertEqual(client.get(f"{BASE}/").status_code, 403)
        self.assertEqual(self.post_json(client, f"{BASE}/disconnect/", self.pair("Lobby", "Main Hall")).status_code, 403)

    @tag("functional")
    def test_toggle_staff_only(self):
        response = self.post_json(self.client, f"{BASE}/{self.rooms['Lobby']}/update/", {"is_restricted": True})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(GalleryRoom.objects.get(name="Lobby").is_restricted)

    @tag("security")
    def test_newly_restricted_room_triggers_logging(self):
        self.post_json(self.client, f"{BASE}/{self.rooms['Lobby']}/update/", {"is_restricted": True})
        record_move(self.guest.pk, self.rooms["Lobby"], self.employee)
        self.assertTrue(SecurityLog.objects.filter(event_type="RESTRICTED_ROOM_ENTRY").exists())

    @tag("security")
    def test_outside_cannot_be_changed(self):
        response = self.post_json(self.client, f"{BASE}/{self.rooms['Outside']}/update/", {"is_restricted": True})
        self.assertEqual(response.status_code, 400)

    @tag("security")
    def test_flag_must_be_boolean(self):
        response = self.post_json(self.client, f"{BASE}/{self.rooms['Lobby']}/update/", {"is_restricted": "yes"})
        self.assertEqual(response.status_code, 400)

    @tag("functional")
    def test_disconnect_and_reconnect(self):
        self.post_json(self.client, f"{BASE}/disconnect/", self.pair("Sculptures", "Lecture Hall"))
        self.assertFalse(rooms_are_adjacent(self.rooms["Sculptures"], self.rooms["Lecture Hall"]))
        self.post_json(self.client, f"{BASE}/connect/", self.pair("Lecture Hall", "Sculptures"))
        self.assertTrue(rooms_are_adjacent(self.rooms["Sculptures"], self.rooms["Lecture Hall"]))

    @tag("functional")
    def test_cannot_strand_a_room(self):
        self.post_json(self.client, f"{BASE}/disconnect/", self.pair("Storage", "Modern Art"))
        response = self.post_json(self.client, f"{BASE}/disconnect/", self.pair("Storage", "Portrait Hall"))
        self.assertEqual(response.status_code, 400)
        self.assertTrue(rooms_are_adjacent(self.rooms["Storage"], self.rooms["Portrait Hall"]))

    @tag("functional")
    def test_room_cannot_connect_to_itself(self):
        response = self.post_json(self.client, f"{BASE}/connect/", self.pair("Lobby", "Lobby"))
        self.assertEqual(response.status_code, 400)
