import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from accounts.views import role_required

from .services import MovementError, record_move


def _valid_id(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


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