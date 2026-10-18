from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Now


# Models for the gallery app, representing rooms, adjacency, and movement events
class GalleryRoom(models.Model):
    room_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    is_restricted = models.BooleanField(default=False)

    class Meta:
        db_table = "gallery_rooms"

    def __str__(self):
        return self.name


# Junction table for adjacent rooms, ensuring that each connection is stored only once
class AdjacentRoom(models.Model):
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


# Model for movement events, capturing the transition of a person from one room to another
class MovementEvent(models.Model):
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

    # Meta class to define database table name, constraints, and indexes for the MovementEvent model
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
