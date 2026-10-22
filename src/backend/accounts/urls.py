from django.urls import path

from . import views

# URLs for the authentication system
urlpatterns = [
    path("csrf/", views.csrf_view, name="csrf"),
    path("login/", views.login_view, name="login"),
    path("verify-mfa/", views.verify_mfa_view, name="verify-mfa"),
    path("logout/", views.logout_view, name="logout"),
    path("admin-test/", views.admin_test_view, name="admin-test"),
    path("register/", views.register_view, name="register"),
    path("me/", views.me_view, name="me"),
    path("delete-account/", views.delete_account_view, name="delete_account"),
    path("profile/", views.profile_view, name="profile"),
    path("admin/accounts/", views.admin_accounts_view, name="admin_accounts"),
    path("admin/accounts/create/", views.admin_create_account_view, name="admin_create_account"),
]