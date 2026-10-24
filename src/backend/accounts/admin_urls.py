from django.urls import path

from . import admin_views

urlpatterns = [
    path("", admin_views.list_accounts_view, name="admin_accounts"),
    path("create/", admin_views.create_account_view, name="admin_create_account"),
    path("<int:user_id>/", admin_views.account_detail_view, name="admin_account_detail"),
    path("<int:user_id>/update/", admin_views.update_account_view, name="admin_update_account"),
    path("<int:user_id>/reset-mfa/", admin_views.reset_mfa_view, name="admin_reset_mfa"),
    path("<int:user_id>/delete/", admin_views.delete_account_view, name="admin_delete_account"),
]