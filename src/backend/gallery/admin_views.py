import json
from collections import deque

from django.db import transaction
from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from accounts.models import OUTSIDE_ROOM_NAME
from accounts.views import role_required
from audit.utils import log_event

from .models import AdjacentRoom, GalleryRoom


def _json_body(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _valid_id(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _all_rooms_reachable(edges, room_ids, outside_id):
    neighbors = {room_id: set() for room_id in room_ids}
    for a, b in edges:
        neighbors[a].add(b)
        neighbors[b].add(a)
    seen, queue = {outside_id}, deque([outside_id])
    while queue:
        for nxt in neighbors[queue.popleft()] - seen:
            seen.add(nxt)
            queue.append(nxt)
    return seen == set(room_ids)


@require_GET
@role_required("ADMIN")
def list_rooms_view(request):
    rooms = GalleryRoom.objects.annotate(occupants_count=Count("occupants")).order_by("name")
    connections = AdjacentRoom.objects.select_related("room_a", "room_b").order_by("room_a__name", "room_b__name")
    log_event(request, "DATA_QUERY", user=request.user, details="table=gallery_rooms")
    return JsonResponse(
        {
            "rooms": [
                {"room_id": r.room_id, "name": r.name, "is_restricted": r.is_restricted,
                 "occupants": r.occupants_count}
                for r in rooms
            ],
            "connections": [
                {"room_a": {"room_id": c.room_a_id, "name": c.room_a.name},
                 "room_b": {"room_id": c.room_b_id, "name": c.room_b.name}}
                for c in connections
            ],
        },
        status=200,
    )


@require_POST
@role_required("ADMIN")
def update_room_view(request, room_id):
    data = _json_body(request)
    if data is None or not isinstance(data.get("is_restricted"), bool):
        return JsonResponse({"error": "is_restricted must be true or false."}, status=400)

    room = GalleryRoom.objects.filter(pk=room_id).first()
    if room is None:
        return JsonResponse({"error": "Room not found."}, status=404)
    if room.name == OUTSIDE_ROOM_NAME:
        return JsonResponse({"error": "Outside cannot be changed."}, status=400)

    if room.is_restricted != data["is_restricted"]:
        room.is_restricted = data["is_restricted"]
        room.save(update_fields=["is_restricted"])
        log_event(request, "ROOM_MODIFIED", user=request.user,
                  details=f"room={room.name}; is_restricted={room.is_restricted}")
    return JsonResponse({"room_id": room.pk, "name": room.name, "is_restricted": room.is_restricted}, status=200)


def _connection_request(request):
    """(room_a_id, room_b_id) ordered smaller-first, or an error response."""
    data = _json_body(request)
    if data is None:
        return None, JsonResponse({"error": "Invalid request."}, status=400)
    a, b = data.get("room_a_id"), data.get("room_b_id")
    if not _valid_id(a) or not _valid_id(b):
        return None, JsonResponse({"error": "room_a_id and room_b_id must be positive integers."}, status=400)
    if a == b:
        return None, JsonResponse({"error": "A room cannot connect to itself."}, status=400)
    if GalleryRoom.objects.filter(pk__in=(a, b)).count() != 2:
        return None, JsonResponse({"error": "Room not found."}, status=404)
    return tuple(sorted((a, b))), None


@require_POST
@role_required("ADMIN")
def connect_rooms_view(request):
    pair, error = _connection_request(request)
    if error:
        return error
    _, created = AdjacentRoom.objects.get_or_create(room_a_id=pair[0], room_b_id=pair[1])
    if created:
        names = dict(GalleryRoom.objects.filter(pk__in=pair).values_list("room_id", "name"))
        log_event(request, "ROOMS_CONNECTED", user=request.user,
                  details=f"{names[pair[0]]}<->{names[pair[1]]}")
    return JsonResponse({"message": "Rooms connected."}, status=200)


@require_POST
@role_required("ADMIN")
def disconnect_rooms_view(request):
    pair, error = _connection_request(request)
    if error:
        return error

    with transaction.atomic():
        rooms = list(GalleryRoom.objects.select_for_update().order_by("pk"))
        connection = AdjacentRoom.objects.filter(room_a_id=pair[0], room_b_id=pair[1]).first()
        if connection is None:
            return JsonResponse({"error": "Those rooms are not connected."}, status=400)

        outside_id = next(r.pk for r in rooms if r.name == OUTSIDE_ROOM_NAME)
        remaining = [
            (c.room_a_id, c.room_b_id)
            for c in AdjacentRoom.objects.exclude(room_a_id=pair[0], room_b_id=pair[1])
        ]
        if not _all_rooms_reachable(remaining, [r.pk for r in rooms], outside_id):
            return JsonResponse(
                {"error": "Removing this connection would cut off part of the gallery."}, status=400)

        AdjacentRoom.objects.filter(room_a_id=pair[0], room_b_id=pair[1]).delete()

    names = {r.pk: r.name for r in rooms}
    log_event(request, "ROOMS_DISCONNECTED", user=request.user,
              details=f"{names[pair[0]]}<->{names[pair[1]]}")
    return JsonResponse({"message": "Rooms disconnected."}, status=200)