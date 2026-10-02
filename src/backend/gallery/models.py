from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Now


class GalleryRoom(models.Model):
    """Matches the Gallery Rooms entity. Includes the special Outside room."""

    room_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "gallery_rooms"

    def __str__(self):
        return self.name


class AdjacentRoom(models.Model):
    """Junction table.

    Each connection is stored once, with the smaller room_id in room_a.
    Code that inserts rows must order the pair; code that checks adjacency
    must order the pair the same way before looking it up.
    """

    pk = models.CompositePrimaryKey("room_a", "room_b")
    room_a = models.ForeignKey(
        GalleryRoom, on_delete=models.CASCADE, db_column="room_a", related_name="+"
    )
    room_b = models.ForeignKey(
        GalleryRoom, on_delete=models.CASCADE, db_column="room_b", related_name="+"
    )

    class Meta:
        db_table = "adjacent_rooms"
        constraints = [
            models.CheckConstraint(
                condition=Q(room_a__lt=F("room_b")), name="adjacent_rooms_ordered"
            ),
        ]


class MovementEvent(models.Model):
    """Matches Movement entity.

    Entering the gallery is Outside -> an entrance room; leaving is a
    room -> Outside. Rules the database can't check (adjacency, start_room
    matching the person's current room) are enforced in application code.
    """

    event_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column="user_id",
        related_name="movements",
    )
    start_room = models.ForeignKey(
        GalleryRoom, on_delete=models.PROTECT, db_column="start_room", related_name="+"
    )
    end_room = models.ForeignKey(
        GalleryRoom, on_delete=models.PROTECT, db_column="end_room", related_name="+"
    )
    event_time = models.DateTimeField(db_default=Now())
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column="recorded_by",
        related_name="+",
    )

    class Meta:
        db_table = "movement_events"
        constraints = [
            models.CheckConstraint(
                condition=~Q(start_room=F("end_room")),
                name="movement_events_rooms_differ",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "event_time"], name="movement_events_user_time"),
        ]
