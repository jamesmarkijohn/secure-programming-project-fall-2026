import logging

from accounts.crypto import encrypt
from accounts.models import SYSTEM_ACCOUNT_EMAIL, Account

from .models import SecurityLog

logger = logging.getLogger("security")


# The following functions are utility functions for logging security events and retrieving client IP addresses in the Django application
def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


# The log_event function records security events in the SecurityLog model, attributing them to a user (or the system account if no user is provided)
# Also encrypts the event description and logs a warning message
def log_event(request, event_type, user=None, details=""):
    if user is None:
        user = Account.objects.get(email=SYSTEM_ACCOUNT_EMAIL)

    description = f"ip={client_ip(request)}"
    if details:
        description += f"; {details}"

    SecurityLog.objects.create(
        user=user,
        event_type=event_type,
        event_desc=encrypt(description),
    )
    logger.warning("security event %s for account %s", event_type, user.pk)