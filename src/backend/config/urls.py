from django.urls import include, path

from . import views

urlpatterns = [
    path("api/health/", views.health),
    path("api/auth/", include("accounts.urls")),
    path("api/gallery/", include("gallery.urls")),
    path("api/audit/", include("audit.urls")),
    path("api/admin/accounts/", include("accounts.admin_urls")),
    path("api/admin/rooms/", include("gallery.admin_urls")),
]