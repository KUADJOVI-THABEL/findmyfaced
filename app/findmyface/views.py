# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def index(request):
    return render(request, 'findmyface/index.html')


# @login_required
def get_producer(request):
    events = [
        {
            "event_name": "Event 1",
            "event_date": "2024-06-01",
            "event_description": "Location 1"
        }
    ]
    return render(request, 'findmyface/producer.html', {'events': events})

def create_event(request):
    if request.method == 'POST':
        # Handle event creation logic here
        pass
    return render(request, 'findmyface/create_event.html')