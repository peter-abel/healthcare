from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone

from .models import Doctor, DoctorSchedule
from .serializers import DoctorSerializer, DoctorCreateSerializer, DoctorScheduleSerializer
from appointments.models import Appointment
from appointments.serializers import AppointmentSerializer
from healthcare.permissions import IsPatient, IsDoctor, IsPatientOrDoctor, IsAdminUser
from healthcare.utils import get_cached_data, invalidate_cache_pattern

class DoctorViewSet(viewsets.ModelViewSet):
   
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'specialization', 'phone_number']
    ordering_fields = ['user__last_name', 'user__first_name', 'specialization', 'years_of_experience', 'consultation_fee', 'created_at', 'updated_at']
    
    def get_permissions(self):
        
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsDoctor]
        elif self.action == 'list':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'retrieve':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        
        if self.action == 'create':
            return DoctorCreateSerializer
        return DoctorSerializer
    
    def get_queryset(self):
       
        user = self.request.user
        
        # Cache key based on user ID and query parameters
        cache_key = f'doctors_user_{user.id}_{self.request.query_params}'
        
        # Define the query function
        def get_doctors():
            if hasattr(user, 'doctor'):
                # User is a doctor, return only their profile
                return Doctor.objects.filter(user=user)
            else:
                # User is not a doctor, return all doctors
                return Doctor.objects.all()
        
        # Get cached data or execute query
        return get_cached_data(cache_key, settings.DOCTOR_CACHE_TIMEOUT, get_doctors)
    
    def perform_create(self, serializer):
        
        doctor = serializer.save()
        
        # Invalidate cache
        invalidate_cache_pattern(f'doctors_user_{doctor.user.id}_*')
    
    def perform_update(self, serializer):
        
        doctor = serializer.save()
        
        # Invalidate cache
        invalidate_cache_pattern(f'doctors_user_{doctor.user.id}_*')
    
    def perform_destroy(self, instance):
       
        # Store ID before deletion for cache invalidation
        user_id = instance.user.id
        
        # Delete the doctor
        instance.delete()
        
        # Invalidate cache
        invalidate_cache_pattern(f'doctors_user_{user_id}_*')
    
    @action(detail=True, methods=['get'])
    def schedules(self, request, pk=None):
       
        doctor = self.get_object()
        
        # Cache key
        cache_key = f'schedules_doctor_{doctor.id}'
        
        # Define the query function
        def get_schedules():
            return DoctorSchedule.objects.filter(doctor=doctor).order_by('day_of_week', 'start_time')
        
        # Get cached data or execute query
        schedules = get_cached_data(cache_key, settings.DOCTOR_CACHE_TIMEOUT, get_schedules)
        
        serializer = DoctorScheduleSerializer(schedules, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def appointments(self, request, pk=None):
        
        doctor = self.get_object()
        
        # Check permissions
        if hasattr(request.user, 'doctor') and request.user.doctor.id != doctor.id:
            return Response(
                {'error': 'You do not have permission to view these appointments.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get query parameters
        date_from = request.query_params.get('date_from', timezone.now().date())
        date_to = request.query_params.get('date_to', None)
        status_filter = request.query_params.get('status', None)
        
        # Cache key
        cache_key = f'appointments_doctor_{doctor.id}_{date_from}_{date_to}_{status_filter}'
        
        # Define the query function
        def get_appointments():
            queryset = Appointment.objects.filter(doctor=doctor)
            
            # Apply date filter
            if date_from:
                queryset = queryset.filter(appointment_date__gte=date_from)
            if date_to:
                queryset = queryset.filter(appointment_date__lte=date_to)
            
            # Apply status filter
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            return queryset.order_by('appointment_date', 'appointment_time')
        
        # Get cached data or execute query
        appointments = get_cached_data(cache_key, settings.APPOINTMENT_CACHE_TIMEOUT, get_appointments)
        
        # Paginate and serialize
        page = self.paginate_queryset(appointments)
        if page is not None:
            serializer = AppointmentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def available_slots(self, request, pk=None):
        
        doctor = self.get_object()
        
        # Get query parameters
        date = request.query_params.get('date', timezone.now().date())
        
        # Cache key
        cache_key = f'available_slots_doctor_{doctor.id}_{date}'
        
        # Define the query function
        def get_available_slots():
            # Get the day of the week for the given date
            day_of_week = date.weekday()
            
            # Get the doctor's schedule for that day
            schedule = DoctorSchedule.objects.filter(
                doctor=doctor,
                day_of_week=day_of_week,
                is_available=True
            ).first()
            
            if not schedule:
                return []
            
            # Get all appointments for the doctor on that date
            appointments = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=date
            ).values_list('appointment_time', flat=True)
            
            # Generate available time slots
            import datetime
            slots = []
            current_time = schedule.start_time
            
            # Use 30-minute intervals
            interval = datetime.timedelta(minutes=30)
            
            while current_time <= schedule.end_time:
                # Check if this time slot is already booked
                if current_time not in appointments:
                    slots.append(current_time)
                
                # Move to the next time slot
                current_time = (
                    datetime.datetime.combine(datetime.date.today(), current_time) + interval
                ).time()
            
            return slots
        
        # Get cached data or execute query
        available_slots = get_cached_data(cache_key, settings.APPOINTMENT_CACHE_TIMEOUT, get_available_slots)
        
        return Response({'date': date, 'available_slots': available_slots})

class DoctorScheduleViewSet(viewsets.ModelViewSet):
   
    queryset = DoctorSchedule.objects.all()
    serializer_class = DoctorScheduleSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['day_of_week', 'start_time', 'end_time']
    
    def get_permissions(self):
      
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsDoctor]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
       
        user = self.request.user
        
        # Cache key based on user ID and query parameters
        cache_key = f'schedules_user_{user.id}_{self.request.query_params}'
        
        # Define the query function
        def get_schedules():
            if hasattr(user, 'doctor'):
                # User is a doctor, return their schedules
                return DoctorSchedule.objects.filter(doctor=user.doctor)
            else:
                # User is not a doctor, return schedules for the specified doctor
                doctor_id = self.request.query_params.get('doctor_id', None)
                if doctor_id:
                    return DoctorSchedule.objects.filter(doctor_id=doctor_id)
                return DoctorSchedule.objects.none()
        
        # Get cached data or execute query
        return get_cached_data(cache_key, settings.DOCTOR_CACHE_TIMEOUT, get_schedules)
    
    def perform_create(self, serializer):
        
        #Create a new schedule.
        
        # Get the doctor from the authenticated user
        doctor = get_object_or_404(Doctor, user=self.request.user)
        
        # Save the schedule with the doctor
        schedule = serializer.save(doctor=doctor)
        
        # Invalidate cache
        invalidate_cache_pattern(f'schedules_user_{self.request.user.id}_*')
        invalidate_cache_pattern(f'schedules_doctor_{doctor.id}')
        invalidate_cache_pattern(f'available_slots_doctor_{doctor.id}_*')
    
    def perform_update(self, serializer):
        
        #Update a schedule.
        
        schedule = serializer.save()
        
        # Invalidate cache
        invalidate_cache_pattern(f'schedules_user_{self.request.user.id}_*')
        invalidate_cache_pattern(f'schedules_doctor_{schedule.doctor.id}')
        invalidate_cache_pattern(f'available_slots_doctor_{schedule.doctor.id}_*')
    
    def perform_destroy(self, instance):
        
        #Delete a schedule.
        
        # Store ID before deletion for cache invalidation
        doctor_id = instance.doctor.id
        user_id = instance.doctor.user.id
        
        # Delete the schedule
        instance.delete()
        
        # Invalidate cache
        invalidate_cache_pattern(f'schedules_user_{user_id}_*')
        invalidate_cache_pattern(f'schedules_doctor_{doctor_id}')
        invalidate_cache_pattern(f'available_slots_doctor_{doctor_id}_*')
