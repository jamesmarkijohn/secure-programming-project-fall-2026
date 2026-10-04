from django.urls import include, path

from . import views

urlpatterns = [
    path("api/health/", views.health),
    path("api/auth/", include("accounts.urls")),
]