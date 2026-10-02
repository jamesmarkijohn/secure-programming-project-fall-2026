"""
Field-level encryption for sensitive columns (names, phone numbers, TOTP
secrets, security log details).

Uses Fernet from the `cryptography` library: AES-128-CBC for confidentiality
plus HMAC-SHA256 for integrity, so a tampered ciphertext is rejected instead of
silently decrypting to garbage. The key comes from FIELD_ENCRYPTION_KEY in .env.
"""
from cryptography.fernet import Fernet
from django.conf import settings

_fernet = None


def _get_fernet():
    global _fernet
    if _fernet is None:
        _fernet = Fernet(settings.FIELD_ENCRYPTION_KEY)
    return _fernet


def encrypt(plaintext):
    """str -> bytes (ready to store in a bytea column). None stays None."""
    if plaintext is None:
        return None
    return _get_fernet().encrypt(plaintext.encode("utf-8"))


def decrypt(ciphertext):
    """bytes from a bytea column -> str. None stays None.
    Raises cryptography.fernet.InvalidToken if the data was tampered with
    or encrypted under a different key."""
    if ciphertext is None:
        return None
    return _get_fernet().decrypt(bytes(ciphertext)).decode("utf-8")
