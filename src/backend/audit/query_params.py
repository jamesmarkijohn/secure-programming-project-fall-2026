import re

from django.utils import timezone
from django.utils.dateparse import parse_datetime

PAGE_SIZE = 25
EVENT_TYPE_PATTERN = re.compile(r"^[A-Z_]{1,50}$")


def page_number(request):
    try:
        return max(int(request.GET.get("page", "1")), 1)
    except ValueError:
        return 1


def optional_id(value):
    if value in (None, ""):
        return None
    if not value.isdigit() or int(value) < 1:
        raise ValueError("IDs must be positive integers.")
    return int(value)


def optional_datetime(value):
    if value in (None, ""):
        return None
    try:
        parsed = parse_datetime(value)
    except ValueError:
        parsed = None
    if parsed is None:
        raise ValueError("Dates must be in ISO 8601 format, e.g. 2026-10-24T14:00.")
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_default_timezone())
    return parsed


def optional_event_type(value):
    if value in (None, ""):
        return None
    if not EVENT_TYPE_PATTERN.match(value):
        raise ValueError("Unknown event type.")
    return value