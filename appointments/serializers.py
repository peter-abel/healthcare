from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Appointment
from patients.serializers import PatientSerializer
from doctors.serializers import DoctorSerializer

class AppointmentSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class AppointmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'appointment_date', 'appointment_time', 'reason', 'notes']
    
    def validate(self, data):
        """
        Check that the appointment is valid.
        """
        # Check if appointment is in the past
        from django.utils import timezone
        appointment_datetime = timezone.make_aware(
            timezone.datetime.combine(data['appointment_date'], data['appointment_time'])
        )
        if appointment_datetime <= timezone.now():
            raise serializers.ValidationError("Cannot schedule appointment in the past")
        
        # Check doctor availability
        day_of_week = data['appointment_date'].weekday()
        schedule = data['doctor'].schedules.filter(
            day_of_week=day_of_week,
            is_available=True
        ).first()
        
        if not schedule:
            raise serializers.ValidationError("Doctor is not available on this day")
        
        if not (schedule.start_time <= data['appointment_time'] <= schedule.end_time):
            raise serializers.ValidationError("Appointment time is outside doctor's schedule")
        
        # Check for conflicting appointments
        existing_appointment = Appointment.objects.filter(
            doctor=data['doctor'],
            appointment_date=data['appointment_date'],
            appointment_time=data['appointment_time']
        ).exists()
        
        if existing_appointment:
            raise serializers.ValidationError("This time slot is already booked")
        
        return data

class AppointmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['status', 'notes']
        read_only_fields = ['patient', 'doctor', 'appointment_date', 'appointment_time', 'reason', 'created_at', 'updated_at']

class AppointmentBulkCreateSerializer(serializers.Serializer):
    appointments = AppointmentCreateSerializer(many=True)
    
    def create(self, validated_data):
        appointments_data = validated_data.pop('appointments')
        appointments = []
        
        for appointment_data in appointments_data:
            appointment = Appointment.objects.create(**appointment_data)
            appointments.append(appointment)
        
        return {'appointments': appointments}
