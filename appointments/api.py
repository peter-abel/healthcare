from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Appointment
from .serializers import (
    AppointmentSerializer, 
    AppointmentCreateSerializer, 
    AppointmentUpdateSerializer,
    AppointmentBulkCreateSerializer
)
from patients.models import Patient, MedicalRecord
from doctors.models import Doctor
from healthcare.permissions import IsPatient, IsDoctor, IsPatientOrDoctor
from healthcare.utils import get_cached_data, invalidate_cache_pattern

class AppointmentViewSet(viewsets.ModelViewSet):
    
    #API endpoint for managing appointments.
    
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['patient__user__first_name', 'patient__user__last_name', 'doctor__user__first_name', 'doctor__user__last_name', 'status']
    ordering_fields = ['appointment_date', 'appointment_time', 'created_at', 'updated_at']
    
    def get_permissions(self):
        
        #Instantiates and returns the list of permissions that this view requires.
        
        if self.action == 'create':
            permission_classes = [IsPatient]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsPatientOrDoctor]
        elif self.action == 'bulk_create':
            permission_classes = [IsPatient]
        elif self.action in ['confirm', 'complete', 'cancel']:
            permission_classes = [IsPatientOrDoctor]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        
        #Return appropriate serializer class based on the action.
        
        if self.action == 'create' or self.action == 'bulk_create':
            return AppointmentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AppointmentUpdateSerializer
        return AppointmentSerializer
    
    def get_queryset(self):
        
        #This view should return a list of all appointments
        #for the currently authenticated user.
        
        user = self.request.user
        
        cache_key = f'appointments_user_{user.id}_{self.request.query_params}'
        
        def get_appointments():
            if hasattr(user, 'patient'):
                return Appointment.objects.filter(patient=user.patient)
            elif hasattr(user, 'doctor'):
                return Appointment.objects.filter(doctor=user.doctor)
            else:
                return Appointment.objects.none()
        
        from django.conf import settings
        return get_cached_data(cache_key, settings.APPOINTMENT_CACHE_TIMEOUT, get_appointments)
    
    def perform_create(self, serializer):
        
        #Create a new appointment.
        
        patient = get_object_or_404(Patient, user=self.request.user)
        
        appointment = serializer.save(patient=patient)
        
        # Invalidate cache
        invalidate_cache_pattern(f'appointments_user_{self.request.user.id}_*')
        invalidate_cache_pattern(f'appointments_user_{appointment.doctor.user.id}_*')
        
        # Send notification asynchronously
        from .tasks import notify_doctor_of_new_appointment
        notify_doctor_of_new_appointment.delay(appointment.id)
    
    def perform_update(self, serializer):
        
        #Update an appointment.
        
        old_status = self.get_object().status
        
        # Save the appointment
        appointment = serializer.save()
        
        # Invalidate cache
        invalidate_cache_pattern(f'appointments_user_{appointment.patient.user.id}_*')
        invalidate_cache_pattern(f'appointments_user_{appointment.doctor.user.id}_*')
        
        # If status has changed, send notification asynchronously
        if old_status != appointment.status:
            from .tasks import notify_patient_of_appointment_status_change
            notify_patient_of_appointment_status_change.delay(
                appointment.id, 
                old_status, 
                appointment.status
            )
    
    def perform_destroy(self, instance):
        
        #Delete an appointment.
        
        patient_user_id = instance.patient.user.id
        doctor_user_id = instance.doctor.user.id
        
        instance.delete()
        
        invalidate_cache_pattern(f'appointments_user_{patient_user_id}_*')
        invalidate_cache_pattern(f'appointments_user_{doctor_user_id}_*')
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        
        #Create multiple appointments at once.
        
        serializer = AppointmentBulkCreateSerializer(data=request.data)
        if serializer.is_valid():
            patient = get_object_or_404(Patient, user=request.user)
            
            appointments = []
            for appointment_data in serializer.validated_data['appointments']:
                appointment = Appointment.objects.create(
                    patient=patient,
                    **appointment_data
                )
                appointments.append(appointment)
            
            invalidate_cache_pattern(f'appointments_user_{request.user.id}_*')
            for appointment in appointments:
                invalidate_cache_pattern(f'appointments_user_{appointment.doctor.user.id}_*')
            
            return Response(
                AppointmentSerializer(appointments, many=True).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        
        #Confirm an appointment.
        
        appointment = self.get_object()
        
        if appointment.status != 'SCHEDULED':
            return Response(
                {'error': 'This appointment cannot be confirmed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = appointment.status
        
        appointment.status = 'CONFIRMED'
        appointment.save()
        
        invalidate_cache_pattern(f'appointments_user_{appointment.patient.user.id}_*')
        invalidate_cache_pattern(f'appointments_user_{appointment.doctor.user.id}_*')
        
        # Send notification asynchronously
        from .tasks import notify_patient_of_appointment_status_change
        notify_patient_of_appointment_status_change.delay(
            appointment.id, 
            old_status, 
            appointment.status
        )
        
        # Return the updated appointment
        return Response(AppointmentSerializer(appointment).data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        
        #Mark an appointment as completed.
        
        appointment = self.get_object()
        
        if appointment.status != 'CONFIRMED':
            return Response(
                {'error': 'This appointment cannot be marked as completed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = appointment.status
        
        appointment.status = 'COMPLETED'
        appointment.save()
        
        invalidate_cache_pattern(f'appointments_user_{appointment.patient.user.id}_*')
        invalidate_cache_pattern(f'appointments_user_{appointment.doctor.user.id}_*')
        
        # Send notification asynchronously
        from .tasks import notify_patient_of_appointment_status_change
        notify_patient_of_appointment_status_change.delay(
            appointment.id, 
            old_status, 
            appointment.status
        )
        
        return Response(AppointmentSerializer(appointment).data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        
        #Cancel an appointment.
        
        appointment = self.get_object()
        
        if appointment.status not in ['SCHEDULED', 'CONFIRMED']:
            return Response(
                {'error': 'This appointment cannot be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if appointment.appointment_date < timezone.now().date():
            return Response(
                {'error': 'Past appointments cannot be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Store old status for notification
        old_status = appointment.status
        
        # Cancel appointment
        appointment.status = 'CANCELLED'
        appointment.save()
        
        invalidate_cache_pattern(f'appointments_user_{appointment.patient.user.id}_*')
        invalidate_cache_pattern(f'appointments_user_{appointment.doctor.user.id}_*')
        
        # Send notification asynchronously
        from .tasks import notify_patient_of_appointment_status_change
        notify_patient_of_appointment_status_change.delay(
            appointment.id, 
            old_status, 
            appointment.status
        )
        
        return Response(AppointmentSerializer(appointment).data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        
        #Get upcoming appointments.
        
        queryset = self.get_queryset()
        
        upcoming_appointments = queryset.filter(
            appointment_date__gte=timezone.now().date(),
            status__in=['SCHEDULED', 'CONFIRMED']
        ).order_by('appointment_date', 'appointment_time')
        
        page = self.paginate_queryset(upcoming_appointments)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(upcoming_appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def past(self, request):
        
        #Get past appointments.
        
        queryset = self.get_queryset()
        
        past_appointments = queryset.filter(
            Q(appointment_date__lt=timezone.now().date()) |
            Q(status__in=['COMPLETED', 'CANCELLED', 'NO_SHOW'])
        ).order_by('-appointment_date', '-appointment_time')
        
        page = self.paginate_queryset(past_appointments)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(past_appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        
        #Get today's appointments.
        
        queryset = self.get_queryset()
        
        # Filter for today's appointments
        today_appointments = queryset.filter(
            appointment_date=timezone.now().date()
        ).order_by('appointment_time')
        
        page = self.paginate_queryset(today_appointments)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(today_appointments, many=True)
        return Response(serializer.data)
    
    