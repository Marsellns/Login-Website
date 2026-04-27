"""
seed.py — Skrip Seed Data (Buat User Percobaan)
================================================
Menjalankan skrip ini akan membuat satu user demo:

    Username : demouser
    Password : Demo@2025!
    Email    : demouser@example.com

SECURITY (Salt & Hash):
    User.objects.create_user() secara otomatis:
    1. Menghasilkan SALT acak yang kriptografis kuat via os.urandom()
    2. Meng-hash password dengan Argon2id (dari PASSWORD_HASHERS[0])
    3. Menyimpan format: argon2$argon2id$v=19$m=...,t=...,p=...$<salt>$<hash>
    Password TIDAK PERNAH tersimpan dalam bentuk plaintext.

SECURITY (SQL Injection Prevention):
    User.objects.create_user() dan .filter() menggunakan parameterized queries:
        INSERT INTO auth_user (...) VALUES (%s, %s, %s, ...)
        SELECT 1 FROM auth_user WHERE username = %s LIMIT 1
    Tidak ada raw SQL atau string concatenation.

Cara menjalankan:
    python seed.py  (dari direktori root proyek)
    (pastikan DJANGO_SETTINGS_MODULE sudah diset terlebih dahulu)
"""

import os
import sys
import django

# ── Bootstrap Django ────────────────────────────────────────────────────────────
# Gunakan settings_dev (SQLite) jika DJANGO_SETTINGS_MODULE belum diset
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "secure_auth.settings_dev")

# Tambahkan direktori proyek ke sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

# ── Import model setelah setup ──────────────────────────────────────────────────
from django.contrib.auth.models import User  # noqa: E402

# ── Data user percobaan ─────────────────────────────────────────────────────────
SEED_USERS = [
    {
        "username":   "demouser",
        "email":      "demouser@example.com",
        "password":   "Demo@2025!",   # Akan di-hash dengan Argon2id + salt acak
        "first_name": "Demo",
        "last_name":  "User",
    },
    {
        "username":   "admin",
        "email":      "admin@example.com",
        "password":   "Admin@2025!Secure",
        "first_name": "Admin",
        "last_name":  "Sistem",
        "is_staff":   True,
    },
]


def seed():
    print("=" * 60)
    print("  Seed Data — Sistem Login Aman")
    print("=" * 60)

    for data in SEED_USERS:
        username = data["username"]

        # SECURITY (SQL Injection): .filter(username=username) menghasilkan:
        #     SELECT 1 FROM auth_user WHERE username = %s LIMIT 1
        # Nilai username dikirim sebagai bound parameter — tidak pernah
        # dikoncatenasi ke string SQL.
        if User.objects.filter(username=username).exists():
            print(f"  [SKIP]   User '{username}' sudah ada.")
            continue

        # SECURITY (Salt & Hash): create_user() hashes password secara otomatis
        # menggunakan PASSWORD_HASHERS[0] (Argon2id) + unique random salt.
        user = User.objects.create_user(
            username=data["username"],
            email=data["email"],
            password=data["password"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
        )
        if data.get("is_staff"):
            user.is_staff = True
            user.save()

        print(f"  [OK]     User '{username}' berhasil dibuat.")
        print(f"           Password di-hash dengan Argon2id + salt acak.")

    print()
    print("  Kredensial untuk mencoba login:")
    print("  ┌─────────────┬───────────────────────┐")
    print("  │ Username    │ demouser              │")
    print("  │ Password    │ Demo@2025!            │")
    print("  └─────────────┴───────────────────────┘")
    print()
    print("  Buka: http://127.0.0.1:8000/accounts/login/")
    print("=" * 60)


if __name__ == "__main__":
    seed()
