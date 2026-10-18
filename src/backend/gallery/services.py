from django.db import transaction
from accounts.crypto import encrypt
from accounts.models import SYSTEM_ACCOUNT_EMAIL, Account, Role
from audit.models import SecurityLog
from .models import AdjacentRoom, GalleryRoom, MovementEvent


class MovementError(Exception):
    """Invalid state error."""


# Check if two rooms are adjacent based on their IDs
def rooms_are_adjacent(room_id_1, room_id_2):
    low, high = sorted((room_id_1, room_id_2))
    return AdjacentRoom.objects.filter(room_a_id=low, room_b_id=high).exists()


# Record a movement event for a person moving to a new room, ensuring all constraints are met
# This is how state validation is performed for movement events
def record_move(person_id, end_room_id, recorded_by):
    with transaction.atomic():
        try:
            person = Account.objects.select_for_update().get(pk=person_id)
            end_room = GalleryRoom.objects.get(pk=end_room_id)
        except (Account.DoesNotExist, GalleryRoom.DoesNotExist):
            raise MovementError("Unknown person or room.")

        if person.deleted is not None or person.email == SYSTEM_ACCOUNT_EMAIL:
            raise MovementError("This account cannot be moved.")

        if end_room.pk == person.room_id:
            raise MovementError("The person is already in that room.")

        if not rooms_are_adjacent(person.room_id, end_room.pk):
            raise MovementError("Those rooms are not connected.")

        event = MovementEvent.objects.create(
            user=person,
            start_room_id=person.room_id,
            end_room=end_room,
            recorded_by=recorded_by,
        )

        person.room = end_room
        person.save(update_fields=["room"])

        # Log a security event if a guest enters a restricted room
        if end_room.is_restricted and person.role == Role.GUEST:
            SecurityLog.objects.create(
                user=person,
                event_type="RESTRICTED_ROOM_ENTRY",
                event_desc=encrypt(
                    f"Guest entered {end_room.name} (movement event {event.pk}, "
                    f"recorded by account {recorded_by.pk})"
                ),
            )

        return event