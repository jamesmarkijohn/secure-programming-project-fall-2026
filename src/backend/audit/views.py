from django.http import JsonResponse
from django.views.decorators.http import require_GET

from accounts.crypto import decrypt
from accounts.views import role_required

from .models import SecurityLog
from .query_params import PAGE_SIZE, optional_datetime, optional_event_type, optional_id, page_number
from .ratelimit import over_query_limit
from .utils import log_event


@require_GET
@role_required("ADMIN")
def security_logs_view(request):
    if over_query_limit(request):
        return JsonResponse({"error": "Too many queries. Try again in a minute."}, status=429)

    try:
        event_type = optional_event_type(request.GET.get("event_type"))
        user_id = optional_id(request.GET.get("user_id"))
        since = optional_datetime(request.GET.get("since"))
        until = optional_datetime(request.GET.get("until"))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    logs = SecurityLog.objects.select_related("user")
    applied = []
    if event_type:
        logs = logs.filter(event_type=event_type)
        applied.append(f"event_type={event_type}")
    if user_id:
        logs = logs.filter(user_id=user_id)
        applied.append(f"user={user_id}")
    if since:
        logs = logs.filter(event_time__gte=since)
        applied.append("since")
    if until:
        logs = logs.filter(event_time__lte=until)
        applied.append("until")

    page = page_number(request)
    total = logs.count()
    rows = logs.order_by("-event_time", "-log_id")[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]

    results = []
    for log in rows:
        try:
            description = decrypt(log.event_desc)
        except Exception:
            description = "[Unable to decrypt description]"
        results.append({
            "log_id": log.log_id,
            "user_id": log.user_id,
            "email": log.user.email,
            "event_type": log.event_type,
            "event_desc": description,
            "event_time": log.event_time.isoformat(),
        })

    event_types = list(SecurityLog.objects.order_by("event_type").values_list("event_type", flat=True).distinct())

    log_event(request, "DATA_QUERY", user=request.user,
              details=f"table=security_log; filters={','.join(applied) or 'none'}; page={page}")

    return JsonResponse(
        {"logs": results, "event_types": event_types, "page": page, "page_size": PAGE_SIZE, "total": total},
        status=200,
    )