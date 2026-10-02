"""
Django settings for the backend.

Every secret and environment-specific value is read from environment
variables, which Docker Compose loads from the project's .env file.
"""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def env(name, default=None):
    """Read a setting from the environment. App refuses to start rather 
    than running with a missing secret."""
    value = os.environ.get(name, default)
    if value is None or value == "":
        raise ImproperlyConfigured(f"Required environment variable {name} is not set")
    return value


# Security settings
SECRET_KEY = env("DJANGO_SECRET_KEY")              # signs sessions and CSRF tokens
DEBUG = env("DJANGO_DEBUG", "0") == "1"            # off unless explicitly enabled
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS", "localhost").split(",")

# Key for field-level encryption
FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY")

# Settings for installed applications
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "rest_framework",
    "accounts",
    "gallery",
    "audit",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
TEMPLATES = []  # JSON API only; React renders the pages

# Database settings
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST", "db"),
        "PORT": env("POSTGRES_PORT", "5432"),
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Authentication
AUTH_USER_MODEL = "accounts.Account"

# Argon2id first: used for all new hashes. PBKDF2 listed only so Django
# could still verify (then upgrade) any older hash it encounters.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

# NIST SP 800-63B: minimum 8 characters when the password is one factor of MFA,
# no composition rules, screening against common passwords.
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True
