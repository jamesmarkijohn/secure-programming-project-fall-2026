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
    # ALLOWED_HOSTS is set to localhost by default so that the app can run in dev environment without requiring any additional configuration
    # SECURE_PROXY_SSL_HEADER is set to ensure that Django knows when it's being accessed via HTTPS, even if it's behind a reverse proxy like Caddy
    # SESSION_COOKIE_SECURE, SESSION_COOKIE_HTTPONLY, and SESSION_COOKIE_SAMESITE are set to enhance the security of session cookies
    # SESSION_SAVE_EVERY_REQUEST is set to True to ensure that the session is saved to the database on every request
    # CSRF_COOKIE_SAMESITE is set to "Strict" to prevent the CSRF cookie from being sent in cross-site requests, which helps mitigate CSRF attacks
    # CSRF_COOKIE_SECURE is set to True to ensure that the CSRF cookie is only sent over HTTPS connections
SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS", "localhost").split(",")
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"
SESSION_SAVE_EVERY_REQUEST = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Strict"

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
TEMPLATES = []

# Database settings, credentials pulled from .env
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

# Argon2id will be used for all new passwords, and any existing PBKDF2 hashes will be upgraded to Argon2id on login
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

# NIST SP 800-63B: minimum 8 characters when the password is one factor of MFA, no composition rules, screening against common passwords
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True
