from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
import json
from datetime import timedelta, time  

from .models import Appointment
from patients.models import Patient
from doctors.models import Doctor, DoctorSchedule

class AppointmentModelTests(TestCase):
    def setUp(self):
        # Create test users
        self.patient_user = User.objects.create_user(
            username='testpatient',
            email='patient@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Patient'
        )
        
        self.doctor_user = User.objects.create_user(
            username='testdoctor',
            email='doctor@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Doctor'
        )
        
        # Create patient and doctor
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
        
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization='GENERAL',
            license_number='DOC123456',
            phone_number='+1234567890',
            years_of_experience=5,
            consultation_fee=100.00,
            bio='Test doctor bio'
        )
        
        # Create doctor schedule
        self.schedule = DoctorSchedule.objects.create(
            doctor=self.doctor,
            day_of_week=0,  # Monday
            start_time='09:00:00',
            end_time='17:00:00',
            is_available=True
        )
        
        # Get next Monday
        today = timezone.now().date()
        days_ahead = 0 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        self.next_monday = today + timedelta(days=days_ahead)
        
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=self.next_monday,
            appointment_time=time(10, 0),  
            status='SCHEDULED',
            reason='Test appointment',
            notes='Test notes'
        )
    
    def test_appointment_creation(self):
        """Test that appointment is created correctly"""
        self.assertEqual(self.appointment.patient, self.patient)
        self.assertEqual(self.appointment.doctor, self.doctor)
        self.assertEqual(self.appointment.status, 'SCHEDULED')
    
    def test_appointment_string_representation(self):
        """Test the string representation of an appointment"""
        expected_string = f"{self.patient} with {self.doctor} on {self.next_monday} at 10:00:00"
        self.assertEqual(str(self.appointment), expected_string)
    
    def test_appointment_status_update(self):
        """Test updating appointment status"""
        self.appointment.status = 'CONFIRMED'
        self.appointment.save()
        self.assertEqual(self.appointment.status, 'CONFIRMED')
        
        self.appointment.status = 'COMPLETED'
        self.appointment.save()
        self.assertEqual(self.appointment.status, 'COMPLETED')

class AppointmentAPITests(APITestCase):
    def setUp(self):
        # Create test users
        self.patient_user = User.objects.create_user(
            username='testpatient',
            email='patient@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Patient'
        )
        
        self.doctor_user = User.objects.create_user(
            username='testdoctor',
            email='doctor@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Doctor'
        )
        
        # Create patient and doctor
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
        
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization='GENERAL',
            license_number='DOC123456',
            phone_number='+1234567890',
            years_of_experience=5,
            consultation_fee=100.00,
            bio='Test doctor bio'
        )
        
        # Create doctor schedule
        self.schedule = DoctorSchedule.objects.create(
            doctor=self.doctor,
            day_of_week=0,  # Monday
            start_time='09:00:00',
            end_time='17:00:00',
            is_available=True
        )
        
        # Get next Monday
        today = timezone.now().date()
        days_ahead = 0 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        self.next_monday = today + timedelta(days=days_ahead)
        
        # Create appointment - FIX: Use time object instead of string
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=self.next_monday,
            appointment_time=time(10, 0),  
            status='SCHEDULED',
            reason='Test appointment',
            notes='Test notes'
        )
        
        # URLs
        self.list_url = reverse('appointment-list')
        self.detail_url = reverse('appointment-detail', args=[self.appointment.id])
        self.confirm_url = reverse('appointment-confirm', args=[self.appointment.id])
        self.complete_url = reverse('appointment-complete', args=[self.appointment.id])
        self.cancel_url = reverse('appointment-cancel', args=[self.appointment.id])
    
    def test_get_appointments_as_patient(self):
        """Test that a patient can get their appointments"""
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_get_appointments_as_doctor(self):
        """Test that a doctor can get their appointments"""
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_get_appointment_detail(self):
        """Test getting a specific appointment"""
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.appointment.id)
    
    def test_confirm_appointment(self):
        """Test confirming an appointment"""
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.post(self.confirm_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'CONFIRMED')
    
    def test_complete_appointment(self):
        """Test completing an appointment"""
        # First confirm the appointment
        self.appointment.status = 'CONFIRMED'
        self.appointment.save()
        
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.post(self.complete_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'COMPLETED')
    
    def test_cancel_appointment(self):
        """Test cancelling an appointment"""
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.post(self.cancel_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'CANCELLED')
    


class AppointmentModelTests(TestCase):
    def setUp(self):
        # Create test users
        self.patient_user = User.objects.create_user(
            username='testpatient',
            email='patient@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Patient'
        )
        
        self.doctor_user = User.objects.create_user(
            username='testdoctor',
            email='doctor@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Doctor'
        )
        
        # Create patient and doctor
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
        
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization='GENERAL',
            license_number='DOC123456',
            phone_number='+1234567890',
            years_of_experience=5,
            consultation_fee=100.00,
            bio='Test doctor bio'
        )
        
        # Create doctor schedule
        self.schedule = DoctorSchedule.objects.create(
            doctor=self.doctor,
            day_of_week=0,  # Monday
            start_time='09:00:00',
            end_time='17:00:00',
            is_available=True
        )
        
        # Get next Monday
        today = timezone.now().date()
        days_ahead = 0 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        self.next_monday = today + timedelta(days=days_ahead)
        
        # Create appointment - FIX: Use time object instead of string
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=self.next_monday,
            appointment_time=time(10, 0),  # Changed from '10:00:00' to time(10, 0)
            status='SCHEDULED',
            reason='Test appointment',
            notes='Test notes'
        )
    
    def test_appointment_creation(self):
        """Test that appointment is created correctly"""
        self.assertEqual(self.appointment.patient, self.patient)
        self.assertEqual(self.appointment.doctor, self.doctor)
        self.assertEqual(self.appointment.status, 'SCHEDULED')
    
    def test_appointment_string_representation(self):
        """Test the string representation of an appointment"""
        expected_string = f"{self.patient} with {self.doctor} on {self.next_monday} at 10:00:00"
        self.assertEqual(str(self.appointment), expected_string)
    
    def test_appointment_status_update(self):
        """Test updating appointment status"""
        self.appointment.status = 'CONFIRMED'
        self.appointment.save()
        self.assertEqual(self.appointment.status, 'CONFIRMED')
        
        self.appointment.status = 'COMPLETED'
        self.appointment.save()
        self.assertEqual(self.appointment.status, 'COMPLETED')

class AppointmentAPITests(APITestCase):
    def setUp(self):
        # Create test users
        self.patient_user = User.objects.create_user(
            username='testpatient',
            email='patient@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Patient'
        )
        
        self.doctor_user = User.objects.create_user(
            username='testdoctor',
            email='doctor@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Doctor'
        )
        
        # Create patient and doctor
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
        
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization='GENERAL',
            license_number='DOC123456',
            phone_number='+1234567890',
            years_of_experience=5,
            consultation_fee=100.00,
            bio='Test doctor bio'
        )
        
        # Create doctor schedule
        self.schedule = DoctorSchedule.objects.create(
            doctor=self.doctor,
            day_of_week=0,  # Monday
            start_time='09:00:00',
            end_time='17:00:00',
            is_available=True
        )
        
        # Get next Monday
        today = timezone.now().date()
        days_ahead = 0 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        self.next_monday = today + timedelta(days=days_ahead)
        
        # Create appointment - FIX: Use time object instead of string
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=self.next_monday,
            appointment_time=time(10, 0),  # Changed from '10:00:00' to time(10, 0)
            status='SCHEDULED',
            reason='Test appointment',
            notes='Test notes'
        )
        
        # URLs
        self.list_url = reverse('appointment-list')
        self.detail_url = reverse('appointment-detail', args=[self.appointment.id])
        self.confirm_url = reverse('appointment-confirm', args=[self.appointment.id])
        self.complete_url = reverse('appointment-complete', args=[self.appointment.id])
        self.cancel_url = reverse('appointment-cancel', args=[self.appointment.id])
    
    def test_get_appointments_as_patient(self):
        """Test that a patient can get their appointments"""
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_get_appointments_as_doctor(self):
        """Test that a doctor can get their appointments"""
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_get_appointment_detail(self):
        """Test getting a specific appointment"""
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.appointment.id)
    
    def test_confirm_appointment(self):
        """Test confirming an appointment"""
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.post(self.confirm_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'CONFIRMED')
    
    def test_complete_appointment(self):
        """Test completing an appointment"""
        # First confirm the appointment
        self.appointment.status = 'CONFIRMED'
        self.appointment.save()
        
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.post(self.complete_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'COMPLETED')
    
    def test_cancel_appointment(self):
        """Test cancelling an appointment"""
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.post(self.cancel_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'CANCELLED')
    
    def test_create_appointment(self):
        """Test creating a new appointment"""
        self.client.force_authenticate(user=self.patient_user)
        
        # Get next Tuesday and create schedule for Tuesday
        next_tuesday = self.next_monday + timedelta(days=1)
        
        # Create doctor schedule for Tuesday (day_of_week=1)
        tuesday_schedule = DoctorSchedule.objects.create(
            doctor=self.doctor,
            day_of_week=1,  # Tuesday
            start_time='09:00:00',
            end_time='17:00:00',
            is_available=True
        )
        
        data = {
            'patient': self.patient.id,  
            'doctor': self.doctor.id,
            'appointment_date': next_tuesday.isoformat(),
            'appointment_time': '11:00:00',  # API accepts string format, serializer handles conversion
            'reason': 'New test appointment',
            'notes': 'New test notes'
        }
        
        response = self.client.post(self.list_url, data, format='json')
        
        # Debug: Print response content if test fails
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the appointment was created
        self.assertEqual(Appointment.objects.count(), 2)
        new_appointment = Appointment.objects.get(appointment_date=next_tuesday)
        self.assertEqual(new_appointment.reason, 'New test appointment')
