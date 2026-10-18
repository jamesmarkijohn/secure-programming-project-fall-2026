import json
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from accounts.views import role_required
from .services import MovementError, record_move
from accounts.models import OUTSIDE_ROOM_NAME, SYSTEM_ACCOUNT_EMAIL, Account
from .models import GalleryRoom

def _valid_id(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


# Views for the gallery app, handling movement recording and occupancy information
@require_POST
@role_required("EMPLOYEE", "ADMIN")
def record_move_view(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid request."}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({"error": "Invalid request."}, status=400)

    person_id = data.get("person_id")
    room_id = data.get("room_id")

    if not _valid_id(person_id) or not _valid_id(room_id):
        return JsonResponse({"error": "person_id and room_id must be positive integers."}, status=400)

    try:
        event = record_move(person_id, room_id, recorded_by=request.user)
    except MovementError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse(
        {
            "event_id": event.pk,
            "person_id": person_id,
            "start_room": event.start_room.name,
            "end_room": event.end_room.name,
        },
        status=201,
    )


# Endpoint for users to retrieve their current location (room name)
@require_GET
@role_required("GUEST", "EMPLOYEE", "ADMIN")
def my_location_view(request):
    return JsonResponse({"room": request.user.room.name}, status=200)


# Endpoint for employees and admins to retrieve occupancy information for all rooms
@require_GET
@role_required("EMPLOYEE", "ADMIN")
def occupancy_view(request):
    rooms = {
        room.name: []
        for room in GalleryRoom.objects.exclude(name=OUTSIDE_ROOM_NAME).order_by("name")
    }
    people = (
        Account.objects.filter(deleted__isnull=True)
        .exclude(email=SYSTEM_ACCOUNT_EMAIL)
        .exclude(room__name=OUTSIDE_ROOM_NAME)
        .select_related("room")
        .order_by("email")
    )
    for person in people:
        rooms[person.room.name].append(
            {"user_id": person.pk, "email": person.email, "role": person.role}
        )
    return JsonResponse({"rooms": rooms}, status=200)