from django.urls import path

from . import views

urlpatterns = [
    path("moves/", views.record_move_view, name="record_move"),
    path("my-location/", views.my_location_view, name="my_location"),
    path("occupancy/", views.occupancy_view, name="occupancy"),
]