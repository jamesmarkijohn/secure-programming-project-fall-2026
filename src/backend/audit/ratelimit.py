from datetime import timedelta

from django.utils import timezone

from .models import RateLimitHit
from .utils import client_ip, log_event

LOGIN_LIMIT = 10
LOGIN_WINDOW = timedelta(minutes=5)

QUERY_LIMIT = 10
QUERY_WINDOW = timedelta(minutes=1)


def over_limit(request, scope="login", limit=LOGIN_LIMIT, window=LOGIN_WINDOW, per_ip=True):
    ip = client_ip(request)
    now = timezone.now()

    RateLimitHit.objects.create(ip_address=ip, scope=scope)
    RateLimitHit.objects.filter(scope=scope, created__lt=now - window).delete()

    hits = RateLimitHit.objects.filter(scope=scope, created__gte=now - window)
    if per_ip:
        hits = hits.filter(ip_address=ip)
    count = hits.count()

    if count > limit:
        if count == limit + 1:
            log_event(request, "RATE_LIMITED", details=f"scope={scope}")
        return True
    return False


def over_query_limit(request):
    return over_limit(
        request,
        scope=f"query:{request.user.pk}",
        limit=QUERY_LIMIT,
        window=QUERY_WINDOW,
        per_ip=False,
    )