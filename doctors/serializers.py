from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Doctor, DoctorSchedule

class DoctorUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class DoctorScheduleSerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    
    class Meta:
        model = DoctorSchedule
        fields = '__all__'

class DoctorSerializer(serializers.ModelSerializer):
    user = DoctorUserSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    specialization_display = serializers.CharField(source='get_specialization_display', read_only=True)
    schedules = DoctorScheduleSerializer(many=True, read_only=True)
    
    class Meta:
        model = Doctor
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return f"Dr. {obj.user.first_name} {obj.user.last_name}"

class DoctorCreateSerializer(serializers.ModelSerializer):
    user = DoctorUserSerializer()
    schedules = DoctorScheduleSerializer(many=True, required=False)
    
    class Meta:
        model = Doctor
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        schedules_data = validated_data.pop('schedules', [])
        user = User.objects.create_user(**user_data)
        doctor = Doctor.objects.create(user=user, **validated_data)
        
        for schedule_data in schedules_data:
            DoctorSchedule.objects.create(doctor=doctor, **schedule_data)
        
        return doctor