from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q

from .models import Patient, MedicalRecord
from appointments.models import Appointment

@login_required
def dashboard(request):
    
    try:
        patient = request.user.patient
    except Patient.DoesNotExist:
        messages.error(request, "You don't have a patient profile.")
        return redirect('home')
    
    # Get upcoming appointments
    upcoming_appointments = Appointment.objects.filter(
        patient=patient,
        appointment_date__gte=timezone.now().date(),
        status__in=['SCHEDULED', 'CONFIRMED']
    ).order_by('appointment_date', 'appointment_time')[:5]
    
    # Get recent medical records
    medical_records = MedicalRecord.objects.filter(
        patient=patient
    ).order_by('-created_at')[:5]
    
    context = {
        'patient': patient,
        'upcoming_appointments': upcoming_appointments,
        'medical_records': medical_records,
    }
    
    return render(request, 'patients/dashboard.html', context)

@login_required
def profile(request):
    
    #View for viewing and updating patient profile.
    
    try:
        patient = request.user.patient
    except Patient.DoesNotExist:
        # This shouldn't happen normally as the role selection process creates the profile
        messages.error(request, "You don't have a patient profile.")
        return redirect('role_selection')
    
    if request.method == 'POST':
        # Update user information
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        
        # Check if password is being updated
        password = request.POST.get('password')
        if password:
            confirm_password = request.POST.get('confirm_password')
            if password == confirm_password:
                user.set_password(password)
            else:
                messages.error(request, "Passwords do not match.")
                return redirect('patient_profile')
        
        user.save()
        
        # Update patient information
        patient.date_of_birth = request.POST.get('date_of_birth')
        patient.gender = request.POST.get('gender')
        patient.phone_number = request.POST.get('phone_number')
        patient.address = request.POST.get('address')
        patient.emergency_contact_name = request.POST.get('emergency_contact_name')
        patient.emergency_contact_phone = request.POST.get('emergency_contact_phone')
        patient.insurance_provider = request.POST.get('insurance_provider')
        patient.insurance_policy_number = request.POST.get('insurance_policy_number')
        
        patient.save()
        
        messages.success(request, "Profile updated successfully.")
        if not patient.date_of_birth:  # Check if this is the first time filling out the profile
            messages.info(request, "Welcome! Your profile has been created successfully.")
        return redirect('patient_dashboard')
    
    context = {
        'patient': patient,
        'gender_choices': Patient.GENDER_CHOICES,
    }
    
    return render(request, 'patients/profile.html', context)

