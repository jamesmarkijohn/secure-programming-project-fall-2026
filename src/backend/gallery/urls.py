from django.urls import path

from . import views

urlpatterns = [
    path("moves/", views.record_move_view, name="record_move"),
    path("my-location/", views.my_location_view, name="my_location"),
    path("occupancy/", views.occupancy_view, name="occupancy"),
    path("movement-history/", views.movement_history_view, name="movement_history"),
    path("events/<int:event_id>/delete/", views.delete_event_view, name="delete_event"),
    path("rooms/", views.rooms_view, name="rooms"),
]