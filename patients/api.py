from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.conf import settings

from .models import Patient, MedicalRecord
from .serializers import PatientSerializer, PatientCreateSerializer, MedicalRecordSerializer
from healthcare.permissions import IsPatient, IsDoctor, IsPatientOrDoctor, IsAdminUser
from healthcare.utils import get_cached_data, invalidate_cache_pattern

class PatientViewSet(viewsets.ModelViewSet):
    
    #API endpoint for managing patients.
    
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'phone_number', 'insurance_provider']
    ordering_fields = ['user__last_name', 'user__first_name', 'created_at', 'updated_at']
    
    def get_permissions(self):
        
        #Instantiates and returns the list of permissions that this view requires.
        
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsPatient]
        elif self.action == 'list':
            permission_classes = [IsDoctor | IsAdminUser]
        elif self.action == 'retrieve':
            permission_classes = [IsPatientOrDoctor]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        
        #Return appropriate serializer class based on the action.
        
        if self.action == 'create':
            return PatientCreateSerializer
        return PatientSerializer
    
    def get_queryset(self):
        
        user = self.request.user
        
        # Cache key based on user ID and query parameters
        cache_key = f'patients_user_{user.id}_{self.request.query_params}'
        
        # Define the query function
        def get_patients():
            if hasattr(user, 'patient'):
                # User is a patient, return only their profile
                return Patient.objects.filter(user=user)
            elif hasattr(user, 'doctor') or user.is_staff:
                # User is a doctor or admin, return all patients
                return Patient.objects.all()
            else:
                # User is neither a patient nor a doctor nor an admin
                return Patient.objects.none()
        
        # Get cached data or execute query
        return get_cached_data(cache_key, settings.PATIENT_CACHE_TIMEOUT, get_patients)
    
    def perform_create(self, serializer):
        
        #Create a new patient.
        
        patient = serializer.save()
        
        # Invalidate cache
        invalidate_cache_pattern(f'patients_user_{patient.user.id}_*')
    
    def perform_update(self, serializer):
        
        #Update a patient.
        
        patient = serializer.save()
        
        # Invalidate cache
        invalidate_cache_pattern(f'patients_user_{patient.user.id}_*')
    
    def perform_destroy(self, instance):
        
        #Delete a patient.
        
        # Store ID before deletion for cache invalidation
        user_id = instance.user.id
        
        # Delete the patient
        instance.delete()
        
        # Invalidate cache
        invalidate_cache_pattern(f'patients_user_{user_id}_*')
    
    @action(detail=True, methods=['get'])
    def medical_records(self, request, pk=None):
        
        #Get medical records for a patient.
        
        patient = self.get_object()
        
        # Check permissions
        if hasattr(request.user, 'patient') and request.user.patient.id != patient.id:
            return Response(
                {'error': 'You do not have permission to view these medical records.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Cache key
        cache_key = f'medical_records_patient_{patient.id}'
        
        # Define the query function
        def get_medical_records():
            return MedicalRecord.objects.filter(patient=patient).order_by('-created_at')
        
        # Get cached data or execute query
        medical_records = get_cached_data(cache_key, settings.PATIENT_CACHE_TIMEOUT, get_medical_records)
        
        # Paginate and serialize
        page = self.paginate_queryset(medical_records)
        if page is not None:
            serializer = MedicalRecordSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = MedicalRecordSerializer(medical_records, many=True)
        return Response(serializer.data)

