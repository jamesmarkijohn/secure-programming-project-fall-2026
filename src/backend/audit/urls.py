from django.urls import path
from . import views

urlpatterns = [
    path("security-logs/", views.security_logs_view, name="security_logs"),
]