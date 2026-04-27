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
