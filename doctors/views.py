from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.paginator import Paginator

from .models import Doctor, DoctorSchedule
from appointments.models import Appointment

@login_required
def dashboard(request):
    
    #Doctor dashboard view showing today's appointments and upcoming appointments.
    
    try:
        doctor = request.user.doctor
    except Doctor.DoesNotExist:
        messages.error(request, "You don't have a doctor profile.")
        return redirect('home')
    
    today = timezone.now().date()
    
    # Get today's appointments
    today_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=today
    ).order_by('appointment_time')
    
    # Get upcoming appointments (excluding today)
    upcoming_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date__gt=today,
        status__in=['SCHEDULED', 'CONFIRMED']
    ).order_by('appointment_date', 'appointment_time')[:5]
    
    # Get doctor's schedule
    schedules = DoctorSchedule.objects.filter(doctor=doctor).order_by('day_of_week')
    
    context = {
        'doctor': doctor,
        'today_appointments': today_appointments,
        'upcoming_appointments': upcoming_appointments,
        'schedules': schedules,
    }
    
    return render(request, 'doctors/dashboard.html', context)

@login_required
def profile(request):
    """
    View for viewing and updating doctor profile.
    """
    try:
        doctor = request.user.doctor
    except Doctor.DoesNotExist:
        # This shouldn't happen normally as the role selection process creates the profile
        messages.error(request, "You don't have a doctor profile.")
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
                return redirect('doctor_profile')
        
        user.save()
        
        # Update doctor information
        doctor.specialization = request.POST.get('specialization')
        doctor.license_number = request.POST.get('license_number')
        doctor.phone_number = request.POST.get('phone_number')
        doctor.years_of_experience = request.POST.get('years_of_experience')
        doctor.consultation_fee = request.POST.get('consultation_fee')
        doctor.bio = request.POST.get('bio')
        
        doctor.save()
        
        messages.success(request, "Profile updated successfully.")
        if not doctor.license_number:  # Check if this is the first time filling out the profile
            messages.info(request, "Welcome! Your profile has been created successfully.")
        return redirect('doctor_dashboard')
    
    context = {
        'doctor': doctor,
        'specializations': Doctor.SPECIALIZATIONS,
    }
    
    return render(request, 'doctors/profile.html', context)
@login_required
def manage_schedule(request):
    
    #View for managing doctor's weekly schedule.
    
    try:
        doctor = request.user.doctor
    except Doctor.DoesNotExist:
        messages.error(request, "You don't have a doctor profile.")
        return redirect('home')
    
    if request.method == 'POST':
        # Process schedule updates
        for day_num in range(7):  # 0-6 for Monday-Sunday
            is_available = request.POST.get(f'day_{day_num}_available') is not None
            
            # Get or create schedule for this day
            schedule, created = DoctorSchedule.objects.get_or_create(
                doctor=doctor,
                day_of_week=day_num,
                defaults={
                    'start_time': '09:00',
                    'end_time': '17:00',
                    'is_available': False
                }
            )
            
            # Update schedule
            if is_available:
                schedule.start_time = request.POST.get(f'day_{day_num}_start')
                schedule.end_time = request.POST.get(f'day_{day_num}_end')
                schedule.is_available = True
            else:
                schedule.is_available = False
            
            schedule.save()
        
        messages.success(request, "Schedule updated successfully.")
        return redirect('doctor_dashboard')
    
    # Get current schedules
    schedules_dict = {}
    for schedule in DoctorSchedule.objects.filter(doctor=doctor):
        schedules_dict[schedule.day_of_week] = schedule
    
    # Create a list of days with their schedule data for easy template access
    days_of_week = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    # Process days with schedule information
    days_with_schedules = []
    for day_num, day_name in days_of_week:
        schedule = schedules_dict.get(day_num)
        days_with_schedules.append({
            'day_num': day_num,
            'day_name': day_name,
            'schedule': schedule,
            'is_available': schedule.is_available if schedule else False,
            'start_time': schedule.start_time if schedule else '09:00',
            'end_time': schedule.end_time if schedule else '17:00',
        })
    
    context = {
        'doctor': doctor,
        'schedules': schedules_dict,  # Keep original for backward compatibility if needed
        'days_of_week': days_of_week,
        'days_with_schedules': days_with_schedules,  # New template-friendly data
    }
    
    return render(request, 'doctors/manage_schedule.html', context)



@login_required
def appointments_list(request):
    
    #View for listing all appointments of a doctor.
    
    try:
        doctor = request.user.doctor
    except Doctor.DoesNotExist:
        messages.error(request, "You don't have a doctor profile.")
        return redirect('home')
    
    # Filter appointments
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    appointments = Appointment.objects.filter(doctor=doctor)
    
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    if date_from:
        appointments = appointments.filter(appointment_date__gte=date_from)
    
    if date_to:
        appointments = appointments.filter(appointment_date__lte=date_to)
    
    appointments = appointments.order_by('-appointment_date', '-appointment_time')
    
    # Pagination
    paginator = Paginator(appointments, 10)  # 10 appointments per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'appointments': page_obj,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'status_choices': Appointment.STATUS_CHOICES,
    }
    
    return render(request, 'doctors/appointments_list.html', context)



def doctor_detail(request, doctor_id):
    
    #View for viewing a specific doctor's details.
    
    doctor = get_object_or_404(Doctor, id=doctor_id)
    schedules = DoctorSchedule.objects.filter(doctor=doctor, is_available=True).order_by('day_of_week')
    
    context = {
        'doctor': doctor,
        'schedules': schedules,
    }
    
    return render(request, 'doctors/detail.html', context)
