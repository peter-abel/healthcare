from django.shortcuts import render
from doctors.models import Doctor

def home(request):
    """
    View for the home page.
    """
    # Get a few doctors to display on the home page
    doctors = Doctor.objects.all().order_by('-years_of_experience')[:3]
    
    context = {
        'doctors': doctors
    }
    return render(request, 'home.html', context)

def about(request):
    """
    View for the about page.
    """
    return render(request, 'about.html')
