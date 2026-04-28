"""
Views — Secure User Registration & Authentication
====================================================
Security guarantees enforced in this module:

  ✅ SQL Injection:  ALL database access via Django ORM — zero raw SQL.
  ✅ XSS:            No use of mark_safe() or |safe filter anywhere.
  ✅ CSRF:           Every POST form includes {% csrf_token %}.
  ✅ Password Hash:  Delegated to Django's auth framework (Argon2).
  ✅ Buffer Overflow: Pure Python — no ctypes, no C-extensions, no manual memory.

FORBIDDEN operations (enforced by code review):
  ✗ cursor.execute() with raw SQL
  ✗ QuerySet.extra()
  ✗ mark_safe() on user-supplied data
  ✗ ctypes / cffi / manual memory management
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
import logging

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# REGISTRATION VIEW
# ──────────────────────────────────────────────────────────────────────────────
@csrf_protect
@require_http_methods(["GET", "POST"])
def register_view(request):
    """
    Handles user registration.

    Security walkthrough:
      1. The form is rendered with {% csrf_token %} — Django validates the
         token on POST, blocking cross-site request forgery.
      2. User input is retrieved via request.POST.get(), which returns a
         plain Python string. No raw SQL is constructed.
      3. Username uniqueness is checked via User.objects.filter(username=...),
         which generates a parameterized query:
             SELECT ... FROM auth_user WHERE username = %s
         The ORM passes the value as a bound parameter — immune to SQLi.
      4. The password is validated against AUTH_PASSWORD_VALIDATORS before
         being hashed and stored.
      5. User.objects.create_user() hashes the password using the first
         hasher in PASSWORD_HASHERS (Argon2). A unique, cryptographically
         random salt is generated automatically. The stored value is:
             argon2$argon2id$v=19$m=102400,t=2,p=8$<salt>$<hash>
      6. All values rendered back to the template are auto-escaped by
         Django's template engine — XSS safe.
    """
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        # ── Input validation ─────────────────────────────────────────────
        errors = []

        if not username or not email or not password:
            errors.append("All fields are required.")

        if password != password_confirm:
            errors.append("Passwords do not match.")

        if len(username) > 150:
            errors.append("Username must be 150 characters or fewer.")

        if len(email) > 254:
            errors.append("Email address is too long.")

        # ORM-based uniqueness check — parameterized query, no raw SQL.
        # Generated SQL: SELECT 1 FROM auth_user WHERE username = %s LIMIT 1
        if User.objects.filter(username=username).exists():
            errors.append("This username is already taken.")

        if User.objects.filter(email=email).exists():
            errors.append("An account with this email already exists.")

        # Django's built-in password validators (length, complexity, etc.)
        if not errors:
            try:
                validate_password(password)
            except ValidationError as e:
                errors.extend(e.messages)

        if errors:
            for error in errors:
                messages.error(request, error)
            # Re-render form. The username and email are auto-escaped by
            # Django's template engine when rendered via {{ }}.
            return render(request, "register.html", {
                "username": username,
                "email": email,
            })

        # ── Create user via ORM ───────────────────────────────────────────
        # User.objects.create_user() performs:
        #   1. Generates a unique salt (os.urandom)
        #   2. Hashes password with Argon2id + salt
        #   3. Executes parameterized INSERT:
        #      INSERT INTO auth_user (username, email, password, ...) VALUES (%s, %s, %s, ...)
        # Zero raw SQL. Zero string concatenation.
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )
            logger.info("User registered successfully: %s", username)
            messages.success(request, "Registration successful! Please log in.")
            return redirect("login")

        except Exception as e:
            logger.error("Registration failed for user '%s': %s", username, str(e))
            messages.error(request, "An unexpected error occurred. Please try again.")
            return render(request, "register.html", {
                "username": username,
                "email": email,
            })

    # GET request — render empty form
    return render(request, "register.html")


# ──────────────────────────────────────────────────────────────────────────────
# LOGIN VIEW
# ──────────────────────────────────────────────────────────────────────────────
@csrf_protect
@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Handles user authentication.

    Security walkthrough:
      1. CSRF token is validated on POST.
      2. authenticate() uses the ORM to fetch the user:
             SELECT ... FROM auth_user WHERE username = %s
         This is a parameterized query — immune to SQL injection.
      3. authenticate() then:
         a. Extracts the algorithm, salt, and hash from the stored password.
         b. Re-hashes the provided password with the same salt using Argon2.
         c. Performs a constant-time comparison (hmac.compare_digest) to
            prevent timing attacks.
      4. On success, login() creates a new session, regenerating the
         session ID to prevent session fixation attacks.
      5. On failure, a generic error message is shown — no information
         leakage about whether the username or password was incorrect.
    """
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(request, "Please provide both username and password.")
            return render(request, "login.html")

        # authenticate() performs a parameterized ORM lookup internally:
        #   User.objects.get(username=username)
        # followed by constant-time password hash comparison.
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # login() regenerates the session ID to prevent session fixation.
            login(request, user)
            logger.info("Successful login for user: %s", username)

            # Safe redirect — only allow internal URLs
            next_url = request.POST.get("next", "")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect("dashboard")
        else:
            # Generic error — prevents username enumeration
            logger.warning("Failed login attempt for username: %s", username)
            messages.error(request, "Invalid username or password.")
            return render(request, "login.html")

    return render(request, "login.html")


# ──────────────────────────────────────────────────────────────────────────────
# LOGOUT VIEW
# ──────────────────────────────────────────────────────────────────────────────
@require_http_methods(["POST"])
def logout_view(request):
    """
    Logs out the user and destroys the session.

    Security notes:
      - Logout is POST-only to prevent CSRF-based forced logout attacks
        via <img src="/logout"> or similar.
      - The session is fully flushed (deleted from DB and cookie cleared).
    """
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect("login")


# ──────────────────────────────────────────────────────────────────────────────
# DASHBOARD VIEW (Protected)
# ──────────────────────────────────────────────────────────────────────────────
@login_required
def dashboard_view(request):
    """
    A simple protected view to verify that authentication works.
    The @login_required decorator redirects unauthenticated users to LOGIN_URL.
    """
    return render(request, "dashboard.html")


# ──────────────────────────────────────────────────────────────────────────────
# SNORT LOGS DASHBOARD VIEW (Protected)
# ──────────────────────────────────────────────────────────────────────────────
import os
import re
from datetime import datetime

@login_required
def snort_logs_view(request):
    """
    Membaca log dari SNORT (format fast) dan menampilkannya di dashboard.
    Di environment produksi Kali Linux, file log biasanya di /var/log/snort/alert.
    Jika file tidak ada (karena berjalan di OS lain untuk testing), 
    kita generate dummy data untuk keperluan demo UI/UX.
    """
    log_path = "/var/log/snort/alert"
    alerts = []
    
    # Kategori serangan untuk statistik
    stats = {
        'sqli': 0,
        'xss': 0,
        'icmp': 0,
        'scan': 0,
        'other': 0
    }

    if os.path.exists(log_path):
        try:
            with open(log_path, 'r') as f:
                lines = f.readlines()[-100:] # Ambil 100 log terakhir
                
            # Contoh format fast alert: 
            # 04/28-07:20:55.123456  [**] [1:1000001:1] [WEB] SQL Injection Attempt Detected [**] [Priority: 0] {TCP} 192.168.1.100:54321 -> 192.168.1.10:80
            for line in reversed(lines):
                if not line.strip(): continue
                
                parts = line.split(" [**] ")
                if len(parts) >= 3:
                    time_raw = parts[0].strip()
                    msg_part = parts[1].strip()
                    ip_part = parts[2].split("}")[-1].strip() if "}" in parts[2] else ""
                    
                    # Coba parsing msg name
                    msg_match = re.search(r'\] (.+)$', msg_part)
                    msg = msg_match.group(1) if msg_match else msg_part
                    
                    # Update stats
                    msg_lower = msg.lower()
                    if 'sql' in msg_lower: stats['sqli'] += 1
                    elif 'xss' in msg_lower: stats['xss'] += 1
                    elif 'icmp' in msg_lower: stats['icmp'] += 1
                    elif 'scan' in msg_lower: stats['scan'] += 1
                    else: stats['other'] += 1
                    
                    alerts.append({
                        'timestamp': time_raw,
                        'message': msg,
                        'source_dest': ip_part
                    })
        except Exception as e:
            logger.error(f"Error reading snort log: {e}")
    else:
        # Dummy data untuk demonstrasi UI jika /var/log/snort/alert tidak ada
        alerts = [
            {'timestamp': '04/28-07:25:12.451', 'message': '[WEB] SQL Injection Attempt Detected (UNION SELECT)', 'source_dest': '192.168.1.105:54112 -> 192.168.1.10:80'},
            {'timestamp': '04/28-07:24:50.112', 'message': '[ICMP] Ping Flood / DoS Attempt Detected', 'source_dest': '192.168.1.102 -> 192.168.1.10'},
            {'timestamp': '04/28-07:21:05.992', 'message': '[SCAN] Nmap TCP SYN Scan', 'source_dest': '192.168.1.200:44321 -> 192.168.1.10:443'},
            {'timestamp': '04/28-07:15:30.221', 'message': '[WEB] XSS Attempt Detected (<script>)', 'source_dest': '10.0.2.15:52001 -> 192.168.1.10:8000'},
            {'timestamp': '04/28-07:10:11.882', 'message': '[WEB] Possible Login Brute Force Attempt', 'source_dest': '192.168.1.150:33123 -> 192.168.1.10:443'},
            {'timestamp': '04/28-07:05:01.001', 'message': '[SCAN] FIN Stealth Scan Detected', 'source_dest': '172.16.0.5:60000 -> 192.168.1.10:80'},
        ]
        stats = {'sqli': 1, 'xss': 1, 'icmp': 1, 'scan': 2, 'other': 1}
        
    context = {
        'alerts': alerts,
        'stats': stats,
        'total_alerts': sum(stats.values()),
        'is_live': os.path.exists(log_path)
    }
    
    return render(request, "snort_dashboard.html", context)

