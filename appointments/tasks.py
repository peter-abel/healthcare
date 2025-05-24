from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from .models import Appointment
from datetime import timedelta

@shared_task
def send_appointment_reminder():
    """Send appointment reminders 24 hours before appointment"""
    tomorrow = timezone.now().date() + timedelta(days=1)
    appointments = Appointment.objects.filter(
        appointment_date=tomorrow,
        status__in=['SCHEDULED', 'CONFIRMED']
    )
    
    for appointment in appointments:
        send_mail(
            'Appointment Reminder',
            f'Dear {appointment.patient.user.first_name}, you have an appointment with {appointment.doctor} tomorrow at {appointment.appointment_time}.',
            'noreply@healthcare.com',
            [appointment.patient.user.email],
            fail_silently=False,
        )
    
    return f"Sent {appointments.count()} reminders"
