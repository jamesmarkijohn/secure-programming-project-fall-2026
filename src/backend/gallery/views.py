import json
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from accounts.views import role_required
from .services import MovementError, record_move
from accounts.models import OUTSIDE_ROOM_NAME, SYSTEM_ACCOUNT_EMAIL, Account
from .models import GalleryRoom, MovementEvent
from django.db.models import Q
from audit.query_params import PAGE_SIZE, optional_datetime, optional_id, page_number
from audit.ratelimit import over_query_limit
from audit.utils import log_event


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


@require_GET
@role_required("GUEST", "EMPLOYEE", "ADMIN")
def my_location_view(request):
    return JsonResponse({"room": request.user.room.name}, status=200)


@require_GET
@role_required("EMPLOYEE", "ADMIN")
def occupancy_view(request):
    rooms = {
    room.name: []
    for room in GalleryRoom.objects.order_by("name")
}
    people = (
        Account.objects.filter(deleted__isnull=True)
        .exclude(email=SYSTEM_ACCOUNT_EMAIL)
        .select_related("room")
        .order_by("email")
    )
    for person in people:
        rooms[person.room.name].append(
            {"user_id": person.pk, "email": person.email, "role": person.role}
        )
    return JsonResponse({"rooms": rooms}, status=200)


@require_GET
@role_required("EMPLOYEE", "ADMIN")
def movement_history_view(request):
    if over_query_limit(request):
        return JsonResponse({"error": "Too many queries. Try again in a minute."}, status=429)

    events = MovementEvent.objects.select_related("user", "start_room", "end_room", "recorded_by")
    applied = []

    try:
        person_id = optional_id(request.GET.get("person_id"))
        room_id = optional_id(request.GET.get("room_id"))
        since = optional_datetime(request.GET.get("since"))
        until = optional_datetime(request.GET.get("until"))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    if person_id:
        events = events.filter(user_id=person_id)
        applied.append(f"person={person_id}")
    if room_id:
        events = events.filter(Q(start_room_id=room_id) | Q(end_room_id=room_id))
        applied.append(f"room={room_id}")
    if since:
        events = events.filter(event_time__gte=since)
        applied.append("since")
    if until:
        events = events.filter(event_time__lte=until)
        applied.append("until")

    page = page_number(request)
    total = events.count()
    rows = events.order_by("-event_time", "-event_id")[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]

    log_event(request, "DATA_QUERY", user=request.user,
              details=f"table=movement_events; filters={','.join(applied) or 'none'}; page={page}")

    return JsonResponse(
        {
            "events": [
                {
                    "event_id": e.event_id,
                    "user_id": e.user_id,
                    "email": e.user.email,
                    "start_room": e.start_room.name,
                    "end_room": e.end_room.name,
                    "event_time": e.event_time.isoformat(),
                    "recorded_by": e.recorded_by.email,
                }
                for e in rows
            ],
            "page": page,
            "page_size": PAGE_SIZE,
            "total": total,
        },
        status=200,
    )


@require_POST
@role_required("ADMIN")
def delete_event_view(request, event_id):
    event = MovementEvent.objects.select_related("start_room", "end_room").filter(pk=event_id).first()
    if event is None:
        return JsonResponse({"error": "Event not found."}, status=404)

    summary = (
        f"by admin={request.user.pk}; event={event.pk}; person={event.user_id}; "
        f"{event.start_room.name}->{event.end_room.name}; at={event.event_time.isoformat()}; "
        f"recorded_by={event.recorded_by_id}"
    )
    event.delete()
    log_event(request, "MOVEMENT_EVENT_DELETED", user=request.user, details=summary)
    return JsonResponse({"message": "Event deleted."}, status=200)


@require_GET
@role_required("EMPLOYEE", "ADMIN")
def rooms_view(request):
    rooms = GalleryRoom.objects.order_by("name")
    return JsonResponse(
        {"rooms": [{"room_id": r.room_id, "name": r.name, "is_restricted": r.is_restricted} for r in rooms]},
        status=200,
    )