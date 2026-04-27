"""
settings_dev.py — Override untuk Development Lokal
====================================================
File ini meng-extend settings.py produksi dan meng-override
konfigurasi yang tidak kompatibel dengan environment lokal
(tanpa MySQL, tanpa HTTPS, tanpa env vars wajib).

PERINGATAN: File ini HANYA untuk development. Jangan pernah
digunakan di lingkungan produksi.

Cara pakai:
    python manage.py runserver --settings=secure_auth.settings_dev
    atau set: set DJANGO_SETTINGS_MODULE=secure_auth.settings_dev
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ── SECRET KEY (dev only — nilai ini TIDAK boleh dipakai di produksi) ──────────
# SECURITY: Di produksi, SECRET_KEY wajib dimuat dari environment variable.
#           Di sini kita pakai nilai hardcoded HANYA untuk kemudahan development.
SECRET_KEY = "dev-only-insecure-key-do-not-use-in-production-!@#$%"

# ── Debug mode ─────────────────────────────────────────────────────────────────
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "0.0.0.0"]

# ── Installed Apps ──────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
]

# ── Middleware ──────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",       # SECURITY: CSRF protection
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",  # SECURITY: anti-clickjacking
]

# ── Templates ──────────────────────────────────────────────────────────────────
# SECURITY: DjangoTemplates mengaktifkan auto-escaping secara default.
#           Semua variabel {{ }} di-escape — XSS safe.
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
        },
    },
]

ROOT_URLCONF = "secure_auth.urls"
WSGI_APPLICATION = "secure_auth.wsgi.application"

# ── DATABASE — SQLite untuk development lokal ──────────────────────────────────
# SECURITY (SQL Injection Prevention): Django ORM secara otomatis menggunakan
# Parameterized Queries. Tidak ada raw SQL string concatenation yang diizinkan.
# Generated SQL contoh: SELECT ... FROM auth_user WHERE username = %s
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ── PASSWORD HASHING — Argon2 sebagai hasher utama ─────────────────────────────
# SECURITY (Salt & Hash): Argon2id adalah pemenang Password Hashing Competition.
# Django secara otomatis:
#   1. Menghasilkan SALT acak yang unik untuk setiap password (via os.urandom)
#   2. Menggabungkan salt + password, lalu meng-hash dengan Argon2id
#   3. Menyimpan format: argon2$argon2id$v=19$m=...,t=...,p=...$<salt>$<hash>
#   4. Saat login, mengekstrak salt yang tersimpan, re-hash, dan membandingkan
#      dengan constant-time comparison (mencegah timing attack)
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",   # Utama — butuh argon2-cffi
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",   # Fallback
]

# ── PASSWORD VALIDATION ─────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},   # Diturunkan ke 8 untuk kemudahan dev
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── HTTPS — Dinonaktifkan untuk development HTTP lokal ─────────────────────────
# SECURITY: Di produksi, nilai-nilai ini harus True (lihat settings.py).
#   SECURE_SSL_REDIRECT = True → redirect semua HTTP ke HTTPS
#   SECURE_HSTS_SECONDS = 31536000 → paksa browser hanya gunakan HTTPS selama 1 tahun
SECURE_SSL_REDIRECT = False         # Dev: HTTP diizinkan
SESSION_COOKIE_SECURE = False       # Dev: cookie boleh dikirim via HTTP
CSRF_COOKIE_SECURE = False          # Dev: CSRF cookie boleh via HTTP

# SECURITY: HSTS header tetap didefinisikan di sini sebagai referensi.
# Di produksi, set ke 31536000 (1 tahun).
SECURE_HSTS_SECONDS = 0             # Dev: HSTS dinonaktifkan
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# ── ADDITIONAL SECURITY HEADERS (tetap aktif di dev) ───────────────────────────
# SECURITY (XSS Prevention): Header X-Content-Type-Options mencegah MIME sniffing.
SECURE_CONTENT_TYPE_NOSNIFF = True

# SECURITY: X-Frame-Options: DENY mencegah clickjacking via iframe.
X_FRAME_OPTIONS = "DENY"

# SECURITY (XSS Prevention): Legacy XSS filter header — defense-in-depth.
SECURE_BROWSER_XSS_FILTER = True

# ── COOKIE SECURITY ─────────────────────────────────────────────────────────────
# SECURITY: HttpOnly mencegah JavaScript mengakses cookie session (mitigasi XSS).
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# ── SESSION ─────────────────────────────────────────────────────────────────────
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 1800            # 30 menit
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SAMESITE = "Strict"   # SECURITY: Mencegah CSRF via cross-origin request

# ── BUFFER OVERFLOW PREVENTION ──────────────────────────────────────────────────
# SECURITY: Batasi ukuran maksimal payload request untuk mencegah
#           denial-of-service dan eksploitasi memori berbasis ukuran data besar.
DATA_UPLOAD_MAX_MEMORY_SIZE = 2_621_440   # 2.5 MB (default Django)
DATA_UPLOAD_MAX_NUMBER_FIELDS = 100        # Batasi jumlah field POST

# ── LOGIN / LOGOUT REDIRECTS ────────────────────────────────────────────────────
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/accounts/dashboard/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# ── STATIC FILES ────────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── LOGGING ─────────────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {module}: {message}",
            "style": "{",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "loggers": {
        "accounts": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
