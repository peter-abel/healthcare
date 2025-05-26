from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Count, Q
from django.conf import settings
import logging
import json
from datetime import timedelta

from .models import Appointment
from healthcare.utils import invalidate_cache_pattern

logger = logging.getLogger('django')

@shared_task
def send_appointment_reminder():
    """Send appointment reminders 24 hours before appointment"""
    tomorrow = timezone.now().date() + timedelta(days=1)
    appointments = Appointment.objects.filter(
        appointment_date=tomorrow,
        status__in=['SCHEDULED', 'CONFIRMED']
    )
    
    success_count = 0
    failed_count = 0
    
    for appointment in appointments:
        try:
            send_mail(
                'Appointment Reminder',
                f'Dear {appointment.patient.user.first_name}, you have an appointment with {appointment.doctor} tomorrow at {appointment.appointment_time}.',
                'noreply@healthcare.com',
                [appointment.patient.user.email],
                fail_silently=False,
            )
            success_count += 1
        except Exception as e:
            failed_count += 1
            logger.error(f"Failed to send reminder for appointment {appointment.id}: {str(e)}")
    
    return f"Sent {success_count} reminders, {failed_count} failed"

@shared_task
def process_appointment_status_updates():
    """Update appointment statuses based on date/time"""
    today = timezone.now().date()
    now = timezone.now().time()
    
    # Mark past appointments as 'NO_SHOW' if they were not completed or cancelled
    past_appointments = Appointment.objects.filter(
        Q(appointment_date__lt=today) | 
        Q(appointment_date=today, appointment_time__lt=now),
        status__in=['SCHEDULED', 'CONFIRMED']
    )
    
    updated_count = 0
    for appointment in past_appointments:
        appointment.status = 'NO_SHOW'
        appointment.save()
        
        # Invalidate cache
        invalidate_cache_pattern(f'appointments_user_{appointment.patient.user.id}_*')
        invalidate_cache_pattern(f'appointments_user_{appointment.doctor.user.id}_*')
        
        updated_count += 1
    
    return f"Updated {updated_count} past appointments to NO_SHOW"

@shared_task
def generate_appointment_analytics():
    """Generate analytics data for appointments"""
    # Get appointment counts by status
    status_counts = dict(Appointment.objects.values('status').annotate(count=Count('id')).values_list('status', 'count'))
    
    # Get appointment counts by doctor specialization
    specialization_counts = {}
    for appointment in Appointment.objects.select_related('doctor'):
        spec = appointment.doctor.get_specialization_display()
        if spec in specialization_counts:
            specialization_counts[spec] += 1
        else:
            specialization_counts[spec] = 1
    
    # Get appointment counts by day of week
    day_counts = {}
    for i in range(7):
        day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][i]
        count = Appointment.objects.filter(appointment_date__week_day=i+2).count()  # Django uses 1-7 for Sunday-Saturday
        day_counts[day_name] = count
    
    # Store analytics in cache
    analytics = {
        'status_counts': status_counts,
        'specialization_counts': specialization_counts,
        'day_counts': day_counts,
        'total_appointments': Appointment.objects.count(),
        'generated_at': timezone.now().isoformat()
    }
    
    cache.set('appointment_analytics', json.dumps(analytics), timeout=86400)  # Cache for 24 hours
    
    return "Generated appointment analytics"

@shared_task
def notify_doctor_of_new_appointment(appointment_id):
    """Notify doctor of a new appointment"""
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        send_mail(
            'New Appointment Scheduled',
            f'Dear Dr. {appointment.doctor.user.first_name} {appointment.doctor.user.last_name}, '
            f'a new appointment has been scheduled with {appointment.patient.user.first_name} {appointment.patient.user.last_name} '
            f'on {appointment.appointment_date} at {appointment.appointment_time}.',
            'noreply@healthcare.com',
            [appointment.doctor.user.email],
            fail_silently=False,
        )
        return f"Notified doctor {appointment.doctor.id} of new appointment {appointment_id}"
    except Appointment.DoesNotExist:
        logger.error(f"Appointment {appointment_id} not found for doctor notification")
        return f"Appointment {appointment_id} not found"
    except Exception as e:
        logger.error(f"Failed to notify doctor of appointment {appointment_id}: {str(e)}")
        return f"Failed to notify doctor: {str(e)}"

@shared_task
def notify_patient_of_appointment_status_change(appointment_id, old_status, new_status):
    """Notify patient of an appointment status change"""
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        
        # Skip notification if the appointment is already in the new status
        # This can happen if the task is executed multiple times
        if appointment.status != new_status:
            logger.info(f"Appointment {appointment_id} status is now {appointment.status}, not {new_status}. Skipping notification.")
            return f"Skipped notification for appointment {appointment_id} (status mismatch)"
        
        send_mail(
            f'Appointment Status Updated: {appointment.get_status_display()}',
            f'Dear {appointment.patient.user.first_name}, '
            f'your appointment with Dr. {appointment.doctor.user.first_name} {appointment.doctor.user.last_name} '
            f'on {appointment.appointment_date} at {appointment.appointment_time} '
            f'has been updated from {old_status} to {appointment.get_status_display()}.',
            'noreply@healthcare.com',
            [appointment.patient.user.email],
            fail_silently=False,
        )
        return f"Notified patient {appointment.patient.id} of status change for appointment {appointment_id}"
    except Appointment.DoesNotExist:
        logger.error(f"Appointment {appointment_id} not found for status change notification")
        return f"Appointment {appointment_id} not found"
    except Exception as e:
        logger.error(f"Failed to notify patient of status change for appointment {appointment_id}: {str(e)}")
        return f"Failed to notify patient: {str(e)}"
