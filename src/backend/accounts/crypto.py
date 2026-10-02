"""
Field-level encryption for sensitive columns (names, phone numbers, TOTP
secrets, security log details, etc.).

Uses Fernet from cryptography library: AES-128-CBC for confidentiality
plus HMAC-SHA256 for integrity, so a tampered ciphertext is rejected. 
The key comes from FIELD_ENCRYPTION_KEY in .env.
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
    if plaintext is None:
        return None
    return _get_fernet().encrypt(plaintext.encode("utf-8"))


def decrypt(ciphertext):
    if ciphertext is None:
        return None
    return _get_fernet().decrypt(bytes(ciphertext)).decode("utf-8")
