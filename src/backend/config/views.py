from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health(request):
    """Confirms the request made it through Caddy to Django."""
    return JsonResponse({"status": "ok", "secure": request.is_secure()})