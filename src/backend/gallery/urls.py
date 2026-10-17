from django.urls import path

from . import views

urlpatterns = [
    path("moves/", views.record_move_view, name="record_move"),
]