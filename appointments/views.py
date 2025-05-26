from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q

from .models import Appointment
from doctors.models import Doctor, DoctorSchedule
from patients.models import Patient, MedicalRecord

@login_required
def book_appointment(request):
    """
    View for booking an appointment with any doctor.
    """
    try:
        patient = request.user.patient
    except Patient.DoesNotExist:
        messages.error(request, "You don't have a patient profile.")
        return redirect('home')
    
    # Get all doctors
    doctors = Doctor.objects.all()
    
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        appointment_date_str = request.POST.get('appointment_date')
        appointment_time_str = request.POST.get('appointment_time')
        reason = request.POST.get('reason')
        notes = request.POST.get('notes', '')
        
        # Validate inputs
        if not all([doctor_id, appointment_date_str, appointment_time_str, reason]):
            messages.error(request, "Please fill in all required fields.")
            return redirect('book_appointment')
        
        doctor = get_object_or_404(Doctor, id=doctor_id)
        
        # Convert string inputs to proper date and time objects
        try:
            # Parse date string (expecting format: YYYY-MM-DD)
            appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
            
            # Parse time string (expecting format: HH:MM)
            appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time()
            
            # Validate that the appointment is not in the past
            appointment_datetime = datetime.combine(appointment_date, appointment_time)
            if appointment_datetime < datetime.now():
                messages.error(request, "Cannot book appointments in the past.")
                return redirect('book_appointment')
                
        except ValueError as e:
            messages.error(request, "Invalid date or time format. Please check your inputs.")
            return redirect('book_appointment')
        
        # Create appointment
        try:
            appointment = Appointment(
                patient=patient,
                doctor=doctor,
                appointment_date=appointment_date,  # Now a proper date object
                appointment_time=appointment_time,  # Now a proper time object
                reason=reason,
                notes=notes,
                status='SCHEDULED'
            )
            appointment.save()
            
            # Send confirmation email (would be implemented in a real system)
            # send_appointment_confirmation_email(appointment)
            
            messages.success(request, "Appointment booked successfully.")
            return redirect('appointment_detail', appointment_id=appointment.id)
        except Exception as e:
            messages.error(request, f"Error booking appointment: {str(e)}")
            return redirect('book_appointment')
    
    # Get all specializations for the filter
    specializations = Doctor.SPECIALIZATIONS
    
    context = {
        'doctors': doctors,
        'specializations': specializations,
    }
    
    return render(request, 'appointments/book.html', context)


@login_required
def book_appointment_with_doctor(request, doctor_id):
    """
    View for booking an appointment with a specific doctor.
    """
    try:
        patient = request.user.patient
    except Patient.DoesNotExist:
        messages.error(request, "You don't have a patient profile.")
        return redirect('home')
    
    doctor = get_object_or_404(Doctor, id=doctor_id)
    
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        appointment_date_str = request.POST.get('appointment_date')
        appointment_time_str = request.POST.get('appointment_time')
        reason = request.POST.get('reason')
        notes = request.POST.get('notes', '')
        
        # Validate inputs
        if not all([doctor_id, appointment_date_str, appointment_time_str, reason]):
            messages.error(request, "Please fill in all required fields.")
            return redirect('book_appointment')
        
        doctor = get_object_or_404(Doctor, id=doctor_id)
        
        # Convert string inputs to proper date and time objects
        try:
            # Parse date string (expecting format: YYYY-MM-DD)
            appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
            
            # Parse time string (expecting format: HH:MM)
            appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time()
            
            # Validate that the appointment is not in the past
            appointment_datetime = datetime.combine(appointment_date, appointment_time)
            if appointment_datetime < datetime.now():
                messages.error(request, "Cannot book appointments in the past.")
                return redirect('book_appointment')
                
        except ValueError as e:
            messages.error(request, "Invalid date or time format. Please check your inputs.")
            return redirect('book_appointment')
        
        # Create appointment
        try:
            appointment = Appointment(
                patient=patient,
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                reason=reason,
                notes=notes,
                status='SCHEDULED'
            )
            appointment.save()
            
            # Send confirmation email (would be implemented in a real system)
            # send_appointment_confirmation_email(appointment)
            
            messages.success(request, "Appointment booked successfully.")
            return redirect('appointment_detail', appointment_id=appointment.id)
        except Exception as e:
            messages.error(request, f"Error booking appointment: {str(e)}")
            return redirect('book_appointment_with_doctor', doctor_id=doctor_id)
    
    # Get doctor's schedule
    schedules = DoctorSchedule.objects.filter(doctor=doctor, is_available=True).order_by('day_of_week')
    
    context = {
        'doctor': doctor,
        'schedules': schedules,
    }
    
    return render(request, 'appointments/book_with_doctor.html', context)

@login_required
def appointment_list(request):
    """
    View for listing all appointments of the logged-in user.
    """
    if hasattr(request.user, 'patient'):
        # User is a patient
        patient = request.user.patient
        upcoming_appointments = Appointment.objects.filter(
            patient=patient,
            appointment_date__gte=timezone.now().date()
        ).order_by('appointment_date', 'appointment_time')
        
        past_appointments = Appointment.objects.filter(
            patient=patient,
            appointment_date__lt=timezone.now().date()
        ).order_by('-appointment_date', '-appointment_time')
        
        context = {
            'upcoming_appointments': upcoming_appointments,
            'past_appointments': past_appointments,
        }
        
        return render(request, 'appointments/patient_list.html', context)
    
    elif hasattr(request.user, 'doctor'):
        # User is a doctor
        return redirect('doctor_appointments')
    
    else:
        messages.error(request, "You don't have a patient or doctor profile.")
        return redirect('home')

@login_required
def appointment_detail(request, appointment_id):
    """
    View for viewing a specific appointment's details.
    """
  
    # Check if user is a patient or doctor
    if hasattr(request.user, 'patient'):
        # User is a patient
        appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user.patient)
    elif hasattr(request.user, 'doctor'):
        # User is a doctor
        appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user.doctor)
    else:
        messages.error(request, "You don't have a patient or doctor profile.")
        return redirect('home')
    
    # Check if there's a medical record for this appointment
    try:
        medical_record = MedicalRecord.objects.get(appointment=appointment)
    except MedicalRecord.DoesNotExist:
        medical_record = None
    
    context = {
        'appointment': appointment,
        'medical_record': medical_record,
    }
    
    return render(request, 'appointments/detail.html', context)

@login_required
def cancel_appointment(request, appointment_id):
    """
    View for cancelling an appointment.
    """
    # Check if user is a patient
    if not hasattr(request.user, 'patient'):
        messages.error(request, "Only patients can cancel appointments.")
        return redirect('home')
    
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user.patient)
    
    # Check if appointment can be cancelled
    if appointment.status not in ['SCHEDULED', 'CONFIRMED']:
        messages.error(request, "This appointment cannot be cancelled.")
        return redirect('appointment_detail', appointment_id=appointment.id)
    
    # Check if appointment is in the past
    if appointment.appointment_date < timezone.now().date():
        messages.error(request, "Past appointments cannot be cancelled.")
        return redirect('appointment_detail', appointment_id=appointment.id)
    
    # Cancel appointment
    appointment.status = 'CANCELLED'
    appointment.save()
    
    # Send cancellation email (would be implemented in a real system)
    # send_appointment_cancellation_email(appointment)
    
    messages.success(request, "Appointment cancelled successfully.")
    return redirect('patient_dashboard')

@login_required
def confirm_appointment(request, appointment_id):
    """
    View for confirming an appointment (doctor only).
    """
    # Check if user is a doctor
    if not hasattr(request.user, 'doctor'):
        messages.error(request, "Only doctors can confirm appointments.")
        return redirect('home')
    
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user.doctor)
    
    # Check if appointment can be confirmed
    if appointment.status != 'SCHEDULED':
        messages.error(request, "This appointment cannot be confirmed.")
        return redirect('appointment_detail', appointment_id=appointment.id)
    
    # Confirm appointment
    appointment.status = 'CONFIRMED'
    appointment.save()
    
    # Send confirmation email (would be implemented in a real system)
    # send_appointment_confirmation_email(appointment)
    
    messages.success(request, "Appointment confirmed successfully.")
    return redirect('appointment_detail', appointment_id=appointment.id)

@login_required
def complete_appointment(request, appointment_id):
    """
    View for marking an appointment as completed (doctor only).
    """
    # Check if user is a doctor
    if not hasattr(request.user, 'doctor'):
        messages.error(request, "Only doctors can complete appointments.")
        return redirect('home')
    
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user.doctor)
    
    # Check if appointment can be completed
    if appointment.status != 'CONFIRMED':
        messages.error(request, "This appointment cannot be marked as completed.")
        return redirect('appointment_detail', appointment_id=appointment.id)
    
    # Complete appointment
    appointment.status = 'COMPLETED'
    appointment.save()
    
    messages.success(request, "Appointment marked as completed.")
    return redirect('appointment_detail', appointment_id=appointment.id)

@login_required
def create_medical_record(request, appointment_id):
    """
    View for creating a medical record for an appointment (doctor only).
    """
    # Check if user is a doctor
    if not hasattr(request.user, 'doctor'):
        messages.error(request, "Only doctors can create medical records.")
        return redirect('home')
    
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user.doctor)
    
    # Check if appointment is completed
    if appointment.status != 'COMPLETED':
        messages.error(request, "Medical records can only be created for completed appointments.")
        return redirect('appointment_detail', appointment_id=appointment.id)
    
    # Check if medical record already exists
    try:
        medical_record = MedicalRecord.objects.get(appointment=appointment)
        messages.error(request, "A medical record already exists for this appointment.")
        return redirect('appointment_detail', appointment_id=appointment.id)
    except MedicalRecord.DoesNotExist:
        pass
    
    if request.method == 'POST':
        diagnosis = request.POST.get('diagnosis')
        treatment = request.POST.get('treatment')
        medications = request.POST.get('medications', '')
        notes = request.POST.get('notes', '')
        
        # Validate inputs
        if not all([diagnosis, treatment]):
            messages.error(request, "Please fill in all required fields.")
            return redirect('create_medical_record', appointment_id=appointment.id)
        
        # Create medical record
        try:
            medical_record = MedicalRecord(
                patient=appointment.patient,
                doctor=appointment.doctor,
                appointment=appointment,
                diagnosis=diagnosis,
                treatment=treatment,
                medications=medications,
                notes=notes
            )
            medical_record.save()
            
            messages.success(request, "Medical record created successfully.")
            return redirect('appointment_detail', appointment_id=appointment.id)
        except Exception as e:
            messages.error(request, f"Error creating medical record: {str(e)}")
            return redirect('create_medical_record', appointment_id=appointment.id)
    
    context = {
        'appointment': appointment,
    }
    
    return render(request, 'appointments/medical_record_form.html', context)

@login_required
def edit_medical_record(request, record_id):
    """
    View for editing a medical record (doctor only).
    """
    # Check if user is a doctor
    if not hasattr(request.user, 'doctor'):
        messages.error(request, "Only doctors can edit medical records.")
        return redirect('home')
    
    medical_record = get_object_or_404(MedicalRecord, id=record_id, doctor=request.user.doctor)
    appointment = medical_record.appointment
    
    if request.method == 'POST':
        diagnosis = request.POST.get('diagnosis')
        treatment = request.POST.get('treatment')
        medications = request.POST.get('medications', '')
        notes = request.POST.get('notes', '')
        
        # Validate inputs
        if not all([diagnosis, treatment]):
            messages.error(request, "Please fill in all required fields.")
            return redirect('edit_medical_record', record_id=record_id)
        
        # Update medical record
        try:
            medical_record.diagnosis = diagnosis
            medical_record.treatment = treatment
            medical_record.medications = medications
            medical_record.notes = notes
            medical_record.save()
            
            messages.success(request, "Medical record updated successfully.")
            return redirect('appointment_detail', appointment_id=appointment.id)
        except Exception as e:
            messages.error(request, f"Error updating medical record: {str(e)}")
            return redirect('edit_medical_record', record_id=record_id)
    
    context = {
        'medical_record': medical_record,
        'appointment': appointment,
    }
    
    return render(request, 'appointments/medical_record_form.html', context)
