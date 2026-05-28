# Basic imports
import io
import json
import json
import uuid
import uuid
import zipfile

import numpy as np

# Create your views here.
from django.http import HttpResponse, JsonResponse, JsonResponse
from django.http import FileResponse
from django.conf import settings

from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from pgvector import django

from django.views.decorators.csrf import csrf_protect
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from pgvector.django import CosineDistance  # Handled by pgvector for vector matching

# auths
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password


from .utility import get_face_embeddings

# Import models
from .models import Event, Photo, FaceEmbedding

# import Forms
from .producer_forms import EventCreationForm


def index(request):
    return render(request, "findmyface/index.html")


def download_event_photos_zip(request, event_id):
    # 1. Fetch the photos (adjust the filter to your exact event logic)
    photos = Photo.objects.filter(event_id=event_id)

    # 2. Create an in-memory zip file
    byte_stream = io.BytesIO()

    with zipfile.ZipFile(byte_stream, "w") as zip_file:
        for photo in photos:
            if photo.file:
                # Open the file from storage (works locally or on AWS S3/Azure)
                try:
                    photo_file = photo.file.open("rb")
                    # Get file name or fallback to a default
                    filename = photo.filename or photo.file.name.split("/")[-1]
                    # Write the binary data into the zip folder
                    zip_file.writestr(filename, photo_file.read())
                    photo_file.close()
                except Exception as e:
                    print("Failed to read file for photo:", photo.id)
                    print("Error:", e)
                    continue  # Skip broken images gracefully

    # 3. Rewind the stream pointer to the beginning
    byte_stream.seek(0)

    # 4. Return the file stream back as a downlodable zip response
    response = FileResponse(byte_stream, content_type="application/zip")
    response["Content-Disposition"] = 'attachment; filename="event_photos.zip"'
    return response


# login view
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(
                request,
                "registration/login.html",
                {"error": "Invalid email or password"},
            )

        if check_password(password, user.password):
            login(request, user)
            return redirect(
                "producer"
            )  # Redirect to the homepage after successful login
        else:
            return render(
                request,
                "registration/login.html",
                {"error": "Invalid email or password"},
            )
    return render(request, "registration/login.html")


@login_required
def get_producer(request):
    events = Event.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "findmyface/producer.html", {"events": events})


@login_required
def create_event(request):
    if request.method == "POST":
        # Handle event creation logic here
        form = EventCreationForm(request.POST)
        print("Form data:", request.POST)
        if form.is_valid():
            # Process the valid form data
            print("Yes form is valid")
            print("Event Name:", form.cleaned_data["event_name"])
            print("Event Date:", form.cleaned_data["event_date"])
            print("Event Description:", form.cleaned_data["event_description"])
            event = Event.objects.create(
                event_name=form.cleaned_data["event_name"],
                event_date=form.cleaned_data["event_date"],
                event_description=form.cleaned_data["event_description"],
                user=request.user,  # Assuming you want to associate the event with the logged-in user
            )
            print("Event created:", event)
            return redirect(
                "producer"
            )  # Redirect to the producer page after successful creation
        else:
            print("Form errors:", form.errors)
    else:
        form = EventCreationForm()
    return render(request, "findmyface/create_event.html", {"form": form})


@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, user=request.user)
    if request.method == "POST":
        event.delete()
        return redirect("producer")
    return render(request, "findmyface/confirm_delete.html", {"event": event})


@login_required
def upload_photo(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == "POST":
        uploaded_files = request.FILES.getlist("photos")
        all_photos_created = []

        # 1. Bulk creation/saving of photos
        for file_obj in uploaded_files:
            photo = Photo(
                event=event,
                filename=file_obj.name,
                file=file_obj,
            )
            photo.save()  # Triggers upload path logic and commits to DB
            all_photos_created.append(photo)

        # Use settings bucket name if defined, otherwise fall back to string
        IMAGE_BUCKET_NAME = getattr(
            settings, "AWS_STORAGE_BUCKET_NAME", "your-image-bucket-name"
        )

        # 2. Extract and store face embeddings
        for photo in all_photos_created:
            # Determine image reference based on environment
            if settings.DEBUG:
                # Local environment: Use local physical folder path
                image_ref = photo.file.path
                is_test = True
            else:
                # Production environment: Use S3 object key string
                image_ref = photo.file.name
                is_test = False

            # Call your fixed extractor function
            embeddings = get_face_embeddings(
                key=image_ref, bucket=IMAGE_BUCKET_NAME, ctx_id=-1, test_mode=is_test
            )

            if not embeddings:
                print(f"No faces detected in photo: {photo.filename}")
                continue

            # 3. Store the embeddings into pgvector DB table
            face_embeddings_to_create = []
            for index, embedding in enumerate(embeddings):
                # Ensure embedding is a standard 1D Python list/array for pgvector
                if isinstance(embedding, np.ndarray):
                    embedding_data = embedding.tolist()
                else:
                    embedding_data = embedding

                face_embeddings_to_create.append(
                    FaceEmbedding(
                        photo=photo,
                        embedding=embedding_data,
                        face_index=index,
                        bbox=None,  # Optional: populate this if your model returns boxes
                    )
                )

            # Bulk save faces per photo for optimized database writes
            if face_embeddings_to_create:
                FaceEmbedding.objects.bulk_create(face_embeddings_to_create)

        return redirect("upload_photo", event_id=event_id)

    # GET request behavior
    photos = event.photos.all()
    return render(
        request,
        "findmyface/upload_photos.html",
        {"event_id": event_id, "photos": photos, "error_message": None},
    )



@csrf_protect
def search_face(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == "POST":
        uploaded_file = request.FILES.get("photo")
        if not uploaded_file:
            return JsonResponse({"error": "No image file provided."}, status=400)

        # 1. Save search file temporarily to feed it into your extractor
        temp_name = f"temp_search_{uuid.uuid4().hex}_{uploaded_file.name}"
        saved_path = default_storage.save(
            f"temp/{temp_name}", ContentFile(uploaded_file.read())
        )

        # Determine appropriate reference path depending on settings.DEBUG
        if settings.DEBUG:
            image_ref = default_storage.path(saved_path)
            is_test = True
            bucket_name = "local-dev"
        else:
            image_ref = saved_path
            is_test = False
            bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME", "")

        try:
            # 2. Extract embedding from the search target image
            search_embeddings = get_face_embeddings(
                key=image_ref, bucket=bucket_name, ctx_id=-1, test_mode=is_test
            )

            # Clean up the temporary file from storage immediately
            default_storage.delete(saved_path)

            if not search_embeddings:
                # Return 200 with empty array so frontend gracefully triggers "no matches"
                return JsonResponse({"photos": []})

            # For multi-face images, take the primary (first detected) face to search against
            target_embedding = search_embeddings[0]

            # 3. Query pgvector using Cosine Distance
            # Threshold 0.4 works well for ArcFace/InsightFace (Lower distance = closer match)
            MATCH_THRESHOLD = 0.4

            matching_faces = (
                FaceEmbedding.objects.filter(
                    photo__event=event,
                )
                .annotate(distance=CosineDistance("embedding", target_embedding))
                .filter(distance__lt=MATCH_THRESHOLD)
                .select_related("photo")
                .order_by("distance")
            )

            # 4. De-duplicate photos (in case multiple faces match the same target photo)
            seen_photo_ids = set()
            matched_photos = []

            for face in matching_faces:
                photo_obj = face.photo
                if photo_obj.id not in seen_photo_ids:
                    seen_photo_ids.add(photo_obj.id)
                    matched_photos.append(
                        {
                            "id": photo_obj.id,
                            "url": photo_obj.file.url,  # Matches photo.url in JS template
                            "file_name": photo_obj.filename,  # Matches photo.file_name in JS template
                        }
                    )

            return JsonResponse({"photos": matched_photos})

        except Exception as e:
            print("Error during face search:", e)
            # Fail-safe cleanup
            if default_storage.exists(saved_path):
                default_storage.delete(saved_path)
            return JsonResponse({"error": str(e)}, status=500)

    # Standard GET request handling
    photos = event.photos.all()
    return render(
        request, "findmyface/search_face.html", {"event_id": event_id, "photos": photos}
    )
