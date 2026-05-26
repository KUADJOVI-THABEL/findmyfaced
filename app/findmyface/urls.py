from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("producer/", views.get_producer, name="producer"),
    path("producer/create-event/", views.create_event, name="create_event"),
]