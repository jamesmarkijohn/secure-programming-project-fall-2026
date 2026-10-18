from datetime import timedelta

from django.utils import timezone

from .models import RateLimitHit
from .utils import client_ip, log_event

# Constants for rate limiting login attempts
LOGIN_LIMIT = 10
LOGIN_WINDOW = timedelta(minutes=5)


# Function to check if a request has exceeded the rate limit for a given scope
def over_limit(request, scope="login", limit=LOGIN_LIMIT, window=LOGIN_WINDOW):
    ip = client_ip(request)
    now = timezone.now()

    RateLimitHit.objects.create(ip_address=ip, scope=scope)
    RateLimitHit.objects.filter(created__lt=now - window).delete()

    count = RateLimitHit.objects.filter(
        scope=scope, ip_address=ip, created__gte=now - window
    ).count()

    if count > limit:
        if count == limit + 1:
            log_event(request, "RATE_LIMITED", details=f"scope={scope}")
        return True
    return False