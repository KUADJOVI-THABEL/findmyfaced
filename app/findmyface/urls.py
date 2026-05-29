from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("producer/", views.get_producer, name="producer"),
    path("producer/create-event/", views.create_event, name="create_event"),
    path("producer/delete_event/<int:event_id>/", views.delete_event, name="delete_event"),
    path("producer/upload-photo/<int:event_id>/", views.upload_photo, name="upload_photo"),
    path("search-face/<int:event_id>/", views.search_face, name="search_face"),

    # Authentication URLs
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Donwload ZIP of all photos for an event
    path('photos/download-zip/<int:event_id>/', views.download_event_photos_zip, name='download_event_photos_zip'),
]