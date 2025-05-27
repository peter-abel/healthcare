from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from datetime import date, timedelta

from .models import Patient, MedicalRecord
from doctors.models import Doctor
from appointments.models import Appointment
from .serializers import PatientSerializer, MedicalRecordSerializer

class PatientModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testpatient',
            email='patient@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='Patient'
        )
        
        self.patient = Patient.objects.create(
            user=self.user,
            date_of_birth='1990-01-01',
            gender='M',
            phone_number='+1234567890',
            address='123 Test St',
            emergency_contact_name='Emergency Contact',
            emergency_contact_phone='+0987654321',
            insurance_provider='Test Insurance',
            insurance_policy_number='ABC123'
        )

    def test_patient_creation(self):
        """Test patient model creation and validation"""
        self.assertEqual(str(self.patient), "Test Patient")
        self.assertEqual(self.patient.user.email, 'patient@example.com')
        self.assertEqual(self.patient.gender, 'M')
        self.assertEqual(self.patient.insurance_provider, 'Test Insurance')

    def test_patient_phone_validation(self):
        """Test phone number validation"""
        # Test invalid phone format
        with self.assertRaises(ValidationError):
            self.patient.phone_number = 'invalid'
            self.patient.full_clean()
        
        with self.assertRaises(ValidationError):
            self.patient.emergency_contact_phone = 'invalid'
            self.patient.full_clean()


class PatientAPITests(APITestCase):
    def setUp(self):
        # Create test user and patient
        self.user = User.objects.create_user(
            username='testpatient',
            email='patient@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='Patient'
        )
        
        self.patient = Patient.objects.create(
            user=self.user,
            date_of_birth='1990-01-01',
            gender='M',
            phone_number='+1234567890',
            address='123 Test St',
            emergency_contact_name='Emergency Contact',
            emergency_contact_phone='+0987654321',
            insurance_provider='Test Insurance',
            insurance_policy_number='ABC123'
        )
        
        # URLs
        self.list_url = reverse('patient-list')
        self.detail_url = reverse('patient-detail', args=[self.patient.id])
        self.medical_records_url = reverse('patient-medical-records', args=[self.patient.id])
        
        # Authenticate
        self.client.force_authenticate(user=self.user)

    def test_get_patient_profile(self):
        """Test retrieving patient profile"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['insurance_policy_number'], 'ABC123')

    def test_update_patient(self):
        """Test updating patient information"""
        data = {
            'address': 'New Address',
            'insurance_provider': 'New Insurance'
        }
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['address'], 'New Address')
        self.assertEqual(response.data['insurance_provider'], 'New Insurance')

    def test_get_medical_records(self):
        """Test retrieving patient's medical records"""
        # Create doctor
        doctor_user = User.objects.create_user(
            username='testdoctor',
            email='doctor@example.com',
            password='TestPass123!'
        )
        
        doctor = Doctor.objects.create(
            user=doctor_user,
            specialization='GENERAL',
            license_number='DOC123456',
            phone_number='+1234567890',
            years_of_experience=5,
            consultation_fee=100.00
        )
        
        # Create medical record
        MedicalRecord.objects.create(
            patient=self.patient,
            doctor=doctor,
            diagnosis='Test diagnosis',
            treatment='Test treatment'
        )
        
        response = self.client.get(self.medical_records_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['diagnosis'], 'Test diagnosis')


      