from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("producer/", views.get_producer, name="producer"),
    path("producer/create-event/", views.create_event, name="create_event"),
    path("producer/upload-photo/<int:event_id>/", views.upload_photo, name="upload_photo"),
    path("search-face/<int:event_id>/", views.search_face, name="search_face"),
]