import re
import unicodedata

FULL_NAME_MAX = 100
PHONE_PATTERN = re.compile(r"^\+?[0-9 ()\-.]+$")


class ProfileError(ValueError):
    """Invalid profile input."""


# Clean and validate the full name and phone number fields for an account profile
def clean_full_name(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ProfileError("Full name must be text.")
    value = " ".join(value.split())
    if not value:
        return None
    if len(value) > FULL_NAME_MAX:
        raise ProfileError(f"Full name must be at most {FULL_NAME_MAX} characters.")
    if any(unicodedata.category(ch) in ("Cc", "Cf") for ch in value):
        raise ProfileError("Full name contains invalid characters.")
    return value


# Clean and validate the phone number field for an account profile
def clean_phone(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ProfileError("Phone number must be text.")
    value = value.strip()
    if not value:
        return None
    digits = sum(ch.isdigit() for ch in value)
    if len(value) > 25 or not PHONE_PATTERN.match(value) or not 7 <= digits <= 15:
        raise ProfileError("Enter a valid phone number.")
    return value