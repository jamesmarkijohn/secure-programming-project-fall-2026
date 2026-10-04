from django.urls import path

from . import views

# URLs for the authentication system
urlpatterns = [
    path("csrf/", views.csrf_view, name="csrf"),
    path("login/", views.login_view, name="login"),
    path("verify-mfa/", views.verify_mfa_view, name="verify-mfa"),
    path("logout/", views.logout_view, name="logout"),
    path("admin-test/", views.admin_test_view, name="admin-test"),
]