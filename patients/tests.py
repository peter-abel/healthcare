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

class MedicalRecordModelTests(TestCase):
    def setUp(self):
        # Create patient
        self.patient_user = User.objects.create_user(
            username='testpatient',
            email='patient@example.com',
            password='TestPass123!'
        )
        
        self.patient = Patient.objects.create(
            user=self.patient_user,
            date_of_birth='1990-01-01',
            gender='M',
            phone_number='+1234567890',
            address='123 Test St',
            emergency_contact_name='Emergency Contact',
            emergency_contact_phone='+0987654321',
            insurance_provider='Test Insurance',
            insurance_policy_number='ABC123'
        )
        
        # Create doctor
        self.doctor_user = User.objects.create_user(
            username='testdoctor',
            email='doctor@example.com',
            password='TestPass123!'
        )
        
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization='GENERAL',
            license_number='DOC123456',
            phone_number='+1234567890',
            years_of_experience=5,
            consultation_fee=100.00
        )
        
        # Create medical record
        self.medical_record = MedicalRecord.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            diagnosis='Test diagnosis',
            treatment='Test treatment',
            medications='Test medications',
            notes='Test notes'
        )

    def test_medical_record_creation(self):
        """Test medical record creation and string representation"""
        self.assertEqual(
            str(self.medical_record),
            f"Record for {self.patient} - {self.medical_record.created_at.date()}"
        )
        self.assertEqual(self.medical_record.diagnosis, 'Test diagnosis')
        self.assertEqual(self.medical_record.treatment, 'Test treatment')

    def test_medical_record_with_appointment(self):
        """Test medical record linked to appointment"""
        future_date = timezone.now() + timedelta(days=1)
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=future_date,
            appointment_time=timezone.now().time(),
            status='COMPLETED',
            reason='Test appointment'
        )
        
        medical_record = MedicalRecord.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment=appointment,
            diagnosis='Follow-up diagnosis',
            treatment='Follow-up treatment'
        )
        
        self.assertEqual(medical_record.appointment, appointment)

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

class MedicalRecordAPITests(APITestCase):
    def setUp(self):
        # Create patient
        self.patient_user = User.objects.create_user(
            username='testpatient',
            email='patient@example.com',
            password='TestPass123!'
        )
        
        self.patient = Patient.objects.create(
            user=self.patient_user,
            date_of_birth='1990-01-01',
            gender='M',
            phone_number='+1234567890',
            address='123 Test St',
            emergency_contact_name='Emergency Contact',
            emergency_contact_phone='+0987654321',
            insurance_provider='Test Insurance',
            insurance_policy_number='ABC123'
        )
        
        # Create doctor
        self.doctor_user = User.objects.create_user(
            username='testdoctor',
            email='doctor@example.com',
            password='TestPass123!'
        )
        
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization='GENERAL',
            license_number='DOC123456',
            phone_number='+1234567890',
            years_of_experience=5,
            consultation_fee=100.00
        )
        
        # Create medical record
        self.medical_record = MedicalRecord.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            diagnosis='Test diagnosis',
            treatment='Test treatment',
            medications='Test medications',
            notes='Test notes'
        )
        
        # URLs
        self.list_url = reverse('medicalrecord-list')
        self.detail_url = reverse('medicalrecord-detail', args=[self.medical_record.id])

    def test_create_medical_record(self):
        """Test creating a new medical record"""
        self.client.force_authenticate(user=self.doctor_user)
        
        data = {
            'patient': self.patient.id,
            'diagnosis': 'New diagnosis',
            'treatment': 'New treatment',
            'medications': 'New medications',
            'notes': 'New notes'
        }
        
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MedicalRecord.objects.count(), 2)
        self.assertEqual(response.data['diagnosis'], 'New diagnosis')

    def test_update_medical_record(self):
        """Test updating a medical record"""
        self.client.force_authenticate(user=self.doctor_user)
        
        data = {
            'diagnosis': 'Updated diagnosis',
            'treatment': 'Updated treatment'
        }
        
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['diagnosis'], 'Updated diagnosis')
        self.assertEqual(response.data['treatment'], 'Updated treatment')

    def test_medical_record_permissions(self):
        """Test medical record access permissions"""
        # Test patient access
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test patient cannot create records
        data = {
            'patient': self.patient.id,
            'diagnosis': 'New diagnosis',
            'treatment': 'New treatment'
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test doctor can create and update
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
