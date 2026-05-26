# Create your views here.
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
# Import models
from .models import Event, Photo, FaceEmbedding
# import Forms
from .producer_forms import EventCreationForm

def index(request):
    return render(request, 'findmyface/index.html')


@login_required
def get_producer(request):
    events = [
        {
            "event_name": "Event 1",
            "event_date": "2024-06-01",
            "event_description": "Location 1"
        }
    ]
    return render(request, 'findmyface/producer.html', {'events': events})

@login_required
def create_event(request):
    if request.method == 'POST':
        # Handle event creation logic here
        form = EventCreationForm(request.POST)
        print("Form data:", request.POST)
        if form.is_valid():
            # Process the valid form data
            print("Yes form is valid")
            print("Event Name:", form.cleaned_data['event_name'])
            print("Event Date:", form.cleaned_data['event_date'])
            print("Event Description:", form.cleaned_data['event_description'])
            event = Event.objects.create(
                event_name=form.cleaned_data['event_name'],
                event_date=form.cleaned_data['event_date'],
                event_description=form.cleaned_data['event_description'],
                user=request.user  # Assuming you want to associate the event with the logged-in user
            )
            return redirect('producer')  # Redirect to the producer page after successful creation
        else:
            print("Form errors:", form.errors)
    else:
        form = EventCreationForm()
    return render(request, 'findmyface/create_event.html', {'form': form})

# upload_photo view to handle photo uploads for an event
# @login_required
def upload_photo(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        uploaded_files = request.FILES.getlist('photos')
        
        # Loop through each individual file in the list
        for file_obj in uploaded_files:
            photo = Photo(
                event=event,
                filename=file_obj.name, # Extracts 'cardboard.png', 'wave.jpg', etc.
                file=file_obj           # Triggers the 'get_upload_path' function
            )
            photo.save() # Saves file payload to Local/S3 and inserts DB record
            
           
        print("Processing file:", uploaded_files)
            # You can also add logic to create FaceEmbedding objects here if needed
        # Handle photo upload logic here
        # You would typically handle the uploaded file, save it to S3, and create a Photo object in the database
        pass
    
    return render(request, 'findmyface/upload_photos.html', {'event_id': event_id})

def search_face(request,event_id):
    # Handle face search logic here
    if request.method == 'POST':
        # Process the uploaded photo and perform face search
        pass
    return render(request, 'findmyface/search_face.html', {'event_id': event_id})