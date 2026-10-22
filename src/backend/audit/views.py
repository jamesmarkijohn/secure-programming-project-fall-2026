from django.http import JsonResponse
from django.views.decorators.http import require_GET

from accounts.views import role_required
from accounts.crypto import decrypt
from .models import SecurityLog


# Only administrators can view security logs
@require_GET
@role_required("ADMIN")
def security_logs_view(request):
    logs = (
        SecurityLog.objects
        .select_related("user")
        .order_by("-event_time", "-log_id")[:100]
    )

    results = []

    for log in logs:
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

    return JsonResponse({"logs": results}, status=200)