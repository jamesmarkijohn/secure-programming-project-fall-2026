from django.urls import path

from . import admin_views

urlpatterns = [
    path("", admin_views.list_rooms_view, name="admin_rooms"),
    path("<int:room_id>/update/", admin_views.update_room_view, name="admin_update_room"),
    path("connect/", admin_views.connect_rooms_view, name="admin_connect_rooms"),
    path("disconnect/", admin_views.disconnect_rooms_view, name="admin_disconnect_rooms"),
]