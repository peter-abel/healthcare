from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class Doctor(models.Model):
    SPECIALIZATIONS = [
        ('CARDIO', 'Cardiology'),
        ('DERMA', 'Dermatology'),
        ('NEURO', 'Neurology'),
        ('ORTHO', 'Orthopedics'),
        ('PEDIA', 'Pediatrics'),
        ('RADIO', 'Radiology'),
        ('GENERAL', 'General Practice'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=10, choices=SPECIALIZATIONS)
    license_number = models.CharField(max_length=50, unique=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$')
    phone_number = models.CharField(validators=[phone_regex], max_length=17)
    years_of_experience = models.PositiveIntegerField(default=1)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name} - {self.get_specialization_display()}"
    
    class Meta:
        ordering = ['user__last_name', 'user__first_name']

class DoctorSchedule(models.Model):
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['doctor', 'day_of_week']
        ordering = ['day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.doctor} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"