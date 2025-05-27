from rest_framework import serializers
from .models import Doctor, DoctorSchedule
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Doctor
        fields = [
            'id', 'user', 'specialization', 'license_number', 
            'phone_number', 'years_of_experience', 'consultation_fee', 
            'bio', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class DoctorCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new doctor profiles"""
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    
    class Meta:
        model = Doctor
        fields = [
            'user', 'specialization', 'license_number', 
            'phone_number', 'years_of_experience', 'consultation_fee', 
            'bio'
        ]
    
    def validate_user(self, value):
        """Ensure user doesn't already have a doctor profile"""
        if hasattr(value, 'doctor'):
            raise serializers.ValidationError("This user already has a doctor profile.")
        return value

class DoctorScheduleSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    
    class Meta:
        model = DoctorSchedule
        fields = ['id', 'doctor', 'day_of_week', 'day_name', 'start_time', 'end_time', 'is_available', 'doctor_name']
        read_only_fields = ['doctor', 'doctor_name', 'day_name']
    
    def validate(self, data):
        """Validate that end time is after start time"""
        if data.get('start_time') and data.get('end_time'):
            if data['end_time'] <= data['start_time']:
                raise serializers.ValidationError("End time must be after start time.")
        return data
    
    def create(self, validated_data):
        """Set the doctor to the current user's doctor profile"""
        user = self.context['request'].user
        try:
            doctor = Doctor.objects.get(user=user)
            validated_data['doctor'] = doctor
        except Doctor.DoesNotExist:
            raise serializers.ValidationError("User must have a doctor profile to create schedules.")
        
        return super().create(validated_data)