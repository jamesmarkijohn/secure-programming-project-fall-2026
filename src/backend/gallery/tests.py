
from django.test import TestCase, tag
from django.urls import reverse

from accounts.models import Account, Role
from gallery.models import GalleryRoom, MovementEvent


class MovementHistoryTests(TestCase):

    def setUp(self):
        self.outside = GalleryRoom.objects.get_or_create(
            name="Outside"
        )[0]

        self.lobby = GalleryRoom.objects.get_or_create(
            name="Lobby"
        )[0]

        self.guest = Account.objects.create_user(
            email="guest-movement@example.com",
            password="GuestTestPassword2026!",
            role=Role.GUEST,
        )

        self.employee = Account.objects.create_user(
            email="employee-movement@example.com",
            password="EmployeeTestPassword2026!",
            role=Role.EMPLOYEE,
        )

        self.admin = Account.objects.create_user(
            email="admin-movement@example.com",
            password="AdminTestPassword2026!",
            role=Role.ADMIN,
        )

        self.url = reverse("movement_history")

    @tag("security")
    def test_guest_cannot_view_movement_history(self):
        self.client.force_login(self.guest)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    @tag("functional")
    def test_employee_can_view_movement_history(self):
        self.client.force_login(self.employee)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    @tag("functional")
    def test_admin_can_view_movement_history(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    @tag("functional")
    def test_movement_history_returns_correct_data(self):
        event = MovementEvent.objects.create(
            user=self.guest,
            start_room=self.outside,
            end_room=self.lobby,
            recorded_by=self.employee,
        )

        self.client.force_login(self.admin)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        events = response.json()["events"]
        self.assertEqual(len(events), 1)

        self.assertEqual(events[0]["event_id"], event.event_id)
        self.assertEqual(events[0]["email"], self.guest.email)
        self.assertEqual(events[0]["start_room"], "Outside")
        self.assertEqual(events[0]["end_room"], "Lobby")
        self.assertEqual(
            events[0]["recorded_by"],
            self.employee.email,
        )
class GalleryOccupancyTests(TestCase):

    def setUp(self):
        self.outside = GalleryRoom.objects.get_or_create(
            name="Outside"
        )[0]

        self.lobby = GalleryRoom.objects.get_or_create(
            name="Lobby"
        )[0]

        self.guest = Account.objects.create_user(
            email="guest-map@example.com",
            password="GuestTestPassword2026!",
            role=Role.GUEST,
        )

        self.employee = Account.objects.create_user(
            email="employee-map@example.com",
            password="EmployeeTestPassword2026!",
            role=Role.EMPLOYEE,
        )

        self.admin = Account.objects.create_user(
            email="admin-map@example.com",
            password="AdminTestPassword2026!",
            role=Role.ADMIN,
        )

        self.url = reverse("occupancy")

    @tag("security")
    def test_guest_cannot_view_occupancy(self):
        self.client.force_login(self.guest)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    @tag("functional")
    def test_employee_can_view_occupancy(self):
        self.client.force_login(self.employee)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    @tag("functional")
    def test_admin_can_view_occupancy(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    @tag("functional")
    def test_occupancy_shows_correct_rooms(self):
        self.guest.room = self.lobby
        self.guest.save(update_fields=["room"])

        self.client.force_login(self.admin)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        rooms = response.json()["rooms"]

        self.assertIn("Outside", rooms)
        self.assertIn("Lobby", rooms)

        lobby_emails = [
            person["email"] for person in rooms["Lobby"]
        ]

        outside_emails = [
            person["email"] for person in rooms["Outside"]
        ]

        self.assertIn(self.guest.email, lobby_emails)
        self.assertIn(self.employee.email, outside_emails)
        self.assertIn(self.admin.email, outside_emails)