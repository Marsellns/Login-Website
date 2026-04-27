"""
Django Settings — Security-Hardened Configuration
===================================================
This file contains ONLY the security-relevant settings, installed apps,
password hashing configuration, and the MySQL DATABASES block.

All other standard Django settings (BASE_DIR, ROOT_URLCONF, TEMPLATES, etc.)
should be present in a full project but are omitted here for clarity.

SECURITY PHILOSOPHY: "Secure by default, explicit over implicit."
"""

import os
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# BASE DIRECTORY
# ──────────────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ──────────────────────────────────────────────────────────────────────────────
# SECRET KEY — MUST be loaded from environment in production
# ──────────────────────────────────────────────────────────────────────────────
# NEVER hard-code the secret key. A leaked SECRET_KEY allows session
# hijacking, CSRF bypass, and arbitrary code execution via pickle-based
# session backends.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError(
        "DJANGO_SECRET_KEY environment variable is not set. "
        "Generate one with: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\""
    )

# ──────────────────────────────────────────────────────────────────────────────
# DEBUG — Explicitly disabled for production
# ──────────────────────────────────────────────────────────────────────────────
DEBUG = False

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")

# ──────────────────────────────────────────────────────────────────────────────
# INSTALLED APPS
# ──────────────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    # Django core apps
    "django.contrib.admin",
    "django.contrib.auth",           # Provides the User model, authentication backend,
    "django.contrib.contenttypes",   # and password hashing infrastructure.
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Project apps
    "accounts",                      # Our custom authentication app
]

# ──────────────────────────────────────────────────────────────────────────────
# MIDDLEWARE
# ──────────────────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",      # Enforces HTTPS redirects, HSTS, etc.
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",          # CSRF protection on all POST requests
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",  # Prevents clickjacking
]

# ──────────────────────────────────────────────────────────────────────────────
# TEMPLATES — Auto-escaping is enabled by default via DjangoTemplates backend
# ──────────────────────────────────────────────────────────────────────────────
# The 'django.template.backends.django.DjangoTemplates' backend enables
# auto-escaping of ALL template variables by default. This is a critical
# XSS mitigation. The |safe filter and mark_safe() are STRICTLY FORBIDDEN
# in any view or template that renders user-supplied data.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            # autoescape=True is the default and MUST NOT be overridden.
        },
    },
]

ROOT_URLCONF = "secure_auth.urls"
WSGI_APPLICATION = "secure_auth.wsgi.application"

# ──────────────────────────────────────────────────────────────────────────────
# DATABASE — MySQL (Production-Ready)
# ──────────────────────────────────────────────────────────────────────────────
# Engine: django.db.backends.mysql uses the `mysqlclient` C library adapter.
#
# Security notes:
#   - Credentials are loaded from environment variables, NEVER hard-coded.
#   - The MySQL user should have ONLY the minimum privileges required
#     (SELECT, INSERT, UPDATE, DELETE on the application database).
#   - The connection uses charset utf8mb4 to prevent encoding-based injection
#     and to support the full Unicode range.
#   - 'init_command' sets the SQL mode to STRICT, which prevents MySQL from
#     silently truncating or coercing data — a defense-in-depth measure
#     against data integrity attacks.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DB_NAME", "secure_auth_db"),
        "USER": os.environ.get("DB_USER", "django_app"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("DB_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            # Enable SSL for the MySQL connection in production:
            # "ssl": {"ca": "/path/to/ca-cert.pem"},
        },
        "CONN_MAX_AGE": 600,  # Persistent connections (10 min) to reduce overhead
    }
}

# ──────────────────────────────────────────────────────────────────────────────
# PASSWORD HASHING — Argon2 as Primary Hasher
# ──────────────────────────────────────────────────────────────────────────────
# Django's password hashing infrastructure works as follows:
#
#   1. When a user is created (User.objects.create_user()), Django invokes
#      the FIRST hasher in PASSWORD_HASHERS to hash the password.
#   2. A UNIQUE, CRYPTOGRAPHICALLY RANDOM SALT is generated for EVERY password.
#      The salt is prepended to the password before hashing and stored alongside
#      the hash in the format: algorithm$iterations$salt$hash
#   3. Upon login (authenticate()), Django retrieves the stored hash, extracts
#      the algorithm and salt, re-hashes the provided password with the same
#      salt, and performs a constant-time comparison.
#   4. If a user's password was hashed with an older algorithm (e.g., PBKDF2),
#      Django will AUTOMATICALLY re-hash it with Argon2 upon next successful
#      login — this is called "hash upgrading."
#
# Argon2id is the winner of the Password Hashing Competition (PHC) and is
# resistant to both GPU-based and side-channel attacks due to its memory-hard
# design.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",   # Primary — requires argon2-cffi
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",   # Fallback for hash upgrades
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]

# ──────────────────────────────────────────────────────────────────────────────
# PASSWORD VALIDATION — Enforce strong passwords
# ──────────────────────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},  # Increased from default 8
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# ──────────────────────────────────────────────────────────────────────────────
# HTTPS / TLS — Secure Communication Settings
# ──────────────────────────────────────────────────────────────────────────────

# SECURE_SSL_REDIRECT = True
# ─────────────────────
# When True, Django's SecurityMiddleware issues a 301 redirect from any
# HTTP request to its HTTPS equivalent. This ensures that NO unencrypted
# communication is ever served, even if a user manually types http://.
# In production behind Nginx (which already terminates TLS), this provides
# a defense-in-depth layer at the application level.
SECURE_SSL_REDIRECT = True

# SESSION_COOKIE_SECURE = True
# ────────────────────────────
# Marks the session cookie with the 'Secure' flag, instructing browsers to
# ONLY transmit it over HTTPS. Without this, a MitM attacker on an HTTP
# connection could steal the session cookie and hijack the user's session.
SESSION_COOKIE_SECURE = True

# CSRF_COOKIE_SECURE = True
# ─────────────────────────
# Same as above but for the CSRF token cookie. Prevents the CSRF token
# from being leaked over unencrypted connections, which would allow an
# attacker to forge cross-site requests.
CSRF_COOKIE_SECURE = True

# SECURE_HSTS_SECONDS = 31536000 (1 year)
# ────────────────────────────────────────
# Sends the HTTP Strict-Transport-Security header, telling browsers to
# ONLY connect to this site via HTTPS for the specified duration.
# Once a browser receives this header, it will refuse to connect over
# plain HTTP — even if the user explicitly types http://.
# CAUTION: Only enable this once HTTPS is fully tested. Misconfiguration
# can lock users out for the entire HSTS duration.
SECURE_HSTS_SECONDS = 31536000  # 1 year

# Include subdomains in the HSTS policy
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Allow the domain to be added to the browser's HSTS preload list
SECURE_HSTS_PRELOAD = True

# ──────────────────────────────────────────────────────────────────────────────
# ADDITIONAL SECURITY HEADERS
# ──────────────────────────────────────────────────────────────────────────────

# Prevents browsers from MIME-sniffing a response away from the declared
# content-type, mitigating drive-by download attacks.
SECURE_CONTENT_TYPE_NOSNIFF = True

# Sets X-Frame-Options to DENY, preventing the site from being embedded
# in iframes — a clickjacking defense.
X_FRAME_OPTIONS = "DENY"

# Instructs browsers to block pages from loading when they detect
# reflected XSS attacks (legacy header, but defense-in-depth).
SECURE_BROWSER_XSS_FILTER = True

# Use HttpOnly flag on session cookies to prevent JavaScript access
SESSION_COOKIE_HTTPONLY = True

# CSRF cookie is HttpOnly by default in Django 4+, but explicit is better
CSRF_COOKIE_HTTPONLY = True

# ──────────────────────────────────────────────────────────────────────────────
# SESSION SECURITY
# ──────────────────────────────────────────────────────────────────────────────
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 1800            # 30 minutes
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SAMESITE = "Strict"   # Prevents CSRF via cross-origin requests

# ──────────────────────────────────────────────────────────────────────────────
# LOGIN REDIRECT
# ──────────────────────────────────────────────────────────────────────────────
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/accounts/dashboard/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# ──────────────────────────────────────────────────────────────────────────────
# STATIC FILES
# ──────────────────────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
