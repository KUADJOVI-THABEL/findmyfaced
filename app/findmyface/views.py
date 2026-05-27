# Basic imports
import io
import zipfile
# Create your views here.
from django.http import HttpResponse
from django.http import FileResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

# auths
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password

# Import models
from .models import Event, Photo, FaceEmbedding

# import Forms
from .producer_forms import EventCreationForm


def index(request):
    return render(request, "findmyface/index.html")


def download_event_photos_zip(request , event_id):
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


# upload_photo view to handle photo uploads for an event
@login_required
def upload_photo(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == "POST":
        uploaded_files = request.FILES.getlist("photos")

        # Loop through each individual file in the list
        for file_obj in uploaded_files:
            photo = Photo(
                event=event,
                filename=file_obj.name,  # Extracts 'cardboard.png', 'wave.jpg', etc.
                file=file_obj,  # Triggers the 'get_upload_path' function
            )
            photo.save()  # Saves file payload to Local/S3 and inserts DB record

        print("Processing file:", uploaded_files)
        # TODO:You can also add logic to create FaceEmbedding objects here if needed
        # Handle photo upload logic here
        # You would typically handle the uploaded file, save it to S3, and create a Photo object in the database
        # redirect to the same page to show the uploaded photos
        return redirect("upload_photo", event_id=event_id)
    # Fetch all photos for the event to display on the page
    photos = event.photos.all()
    return render(
        request,
        "findmyface/upload_photos.html",
        {"event_id": event_id, "photos": photos},
    )


def search_face(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # Handle face search logic here
    if request.method == "POST":
        # Process the uploaded photo and perform face search
        pass
    photos = event.photos.all()
    return render(
        request, "findmyface/search_face.html", {"event_id": event_id, "photos": photos}
    )
