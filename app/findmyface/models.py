from django.db import models
from django.contrib.auth.models import User
# from pgvector.django import VectorField


class Event(models.Model):
    event_name = models.CharField(max_length=255)

    event_description = models.TextField(
        blank=True,
        null=True
    )

    event_date = models.DateTimeField()

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='events'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.event_name


def get_upload_path(instance, filename):
    # This generates exactly: events/<id>/original/<filename>
    return f"events/{instance.event.id}/original/{filename}"

class Photo(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='photos'
    )
    filename = models.CharField(max_length=255)
    # S3 object key
    # example:
    # events/12/original/photo1.jpg
    file = models.FileField(upload_to=get_upload_path, max_length=500)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.filename


class FaceEmbedding(models.Model):
    photo = models.ForeignKey(
        Photo,
        on_delete=models.CASCADE,
        related_name='faces'
    )
    # ArcFace / InsightFace usually use 512 dimensions
    embedding = models.JSONField()
    # Face order inside the image
    # example:
    # first face = 0
    # second face = 1
    face_index = models.IntegerField(default=0)

    # Face bounding box
    # example:
    # {
    #   "x": 120,
    #   "y": 80,
    #   "w": 90,
    #   "h": 90
    # }
    bbox = models.JSONField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Face {self.face_index} - {self.photo.filename}"