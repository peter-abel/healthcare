from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.patients.models import Patient
from apps.doctors.models import Doctor

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='SCHEDULED')
    reason = models.TextField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['doctor', 'appointment_date', 'appointment_time']
        ordering = ['appointment_date', 'appointment_time']
    
    def clean(self):
        # Check if appointment is in the past
        appointment_datetime = timezone.make_aware(
            timezone.datetime.combine(self.appointment_date, self.appointment_time)
        )
        if appointment_datetime <= timezone.now():
            raise ValidationError("Cannot schedule appointment in the past")
        
        # Check doctor availability
        day_of_week = self.appointment_date.weekday()
        schedule = self.doctor.schedules.filter(
            day_of_week=day_of_week,
            is_available=True
        ).first()
        
        if not schedule:
            raise ValidationError("Doctor is not available on this day")
        
        if not (schedule.start_time <= self.appointment_time <= schedule.end_time):
            raise ValidationError("Appointment time is outside doctor's schedule")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.patient} with {self.doctor} on {self.appointment_date} at {self.appointment_time}"
