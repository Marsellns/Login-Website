"""
URL Configuration — Authentication Endpoints
==============================================
All routes use named URL patterns for safe reverse resolution.
No raw SQL or user input is involved in URL routing.
"""

from django.urls import path
from . import views

# App-level URL patterns — included under /accounts/ in the project urls.py
urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("snort-logs/", views.snort_logs_view, name="snort_logs"),
]
