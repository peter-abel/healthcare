from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from datetime import time, timedelta

from .models import Doctor, DoctorSchedule
from .serializers import DoctorSerializer, DoctorScheduleSerializer

class DoctorModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testdoctor',
            email='doctor@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='Doctor'
        )
        
        self.doctor = Doctor.objects.create(
            user=self.user,
            specialization='GENERAL',
            license_number='DOC123456',
            phone_number='+1234567890',
            years_of_experience=5,
            consultation_fee=100.00,
            bio='Test doctor bio'
        )

    def test_doctor_creation(self):
        """Test doctor model creation and validation"""
        self.assertEqual(str(self.doctor), f"Dr. Test Doctor - General Practice")
        self.assertEqual(self.doctor.user.email, 'doctor@example.com')
        self.assertEqual(self.doctor.specialization, 'GENERAL')
        self.assertEqual(self.doctor.consultation_fee, 100.00)

    def test_doctor_phone_validation(self):
        """Test phone number validation"""
        # Test invalid phone format
        with self.assertRaises(ValidationError):
            self.doctor.phone_number = 'invalid'
            self.doctor.full_clean()

class DoctorScheduleModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testdoctor',
            email='doctor@example.com',
            password='TestPass123!'
        )
        
        self.doctor = Doctor.objects.create(
            user=self.user,
            specialization='GENERAL',
            license_number='DOC123456',
            phone_number='+1234567890',
            years_of_experience=5,
            consultation_fee=100.00
        )
        
        self.schedule = DoctorSchedule.objects.create(
            doctor=self.doctor,
            day_of_week=0,  # Monday
            start_time=time(9, 0),  # 9:00 AM
            end_time=time(17, 0),   # 5:00 PM
            is_available=True
        )

    def test_schedule_creation(self):
        """Test schedule creation and string representation"""
        self.assertEqual(
            str(self.schedule),
            f"{self.doctor} - Monday 09:00:00-17:00:00"
        )

    def test_schedule_validation(self):
        """Test schedule validation rules"""
        # Test end time before start time
        with self.assertRaises(ValidationError):
            invalid_schedule = DoctorSchedule(
                doctor=self.doctor,
                day_of_week=1,  # Tuesday
                start_time=time(17, 0),  # 5:00 PM
                end_time=time(9, 0),     # 9:00 AM
                is_available=True
            )
            invalid_schedule.full_clean()

        # Test duplicate schedule for same day
        with self.assertRaises(ValidationError):
            duplicate_schedule = DoctorSchedule(
                doctor=self.doctor,
                day_of_week=0,  # Monday (already exists)
                start_time=time(10, 0),
                end_time=time(18, 0),
                is_available=True
            )
            duplicate_schedule.full_clean()

class DoctorAPITests(APITestCase):
    def setUp(self):
        # Create test user and doctor
        self.user = User.objects.create_user(
            username='testdoctor',
            email='doctor@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='Doctor'
        )
        
        self.doctor = Doctor.objects.create(
            user=self.user,
            specialization='GENERAL',
            license_number='DOC123456',
            phone_number='+1234567890',
            years_of_experience=5,
            consultation_fee=100.00,
            bio='Test doctor bio'
        )
        
        # Create test schedule
        self.schedule = DoctorSchedule.objects.create(
            doctor=self.doctor,
            day_of_week=0,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_available=True
        )
        
        # URLs
        self.list_url = reverse('doctor-list')
        self.detail_url = reverse('doctor-detail', args=[self.doctor.id])
        self.schedules_url = reverse('doctor-schedules', args=[self.doctor.id])
        self.available_slots_url = reverse('doctor-available-slots', args=[self.doctor.id])
        
        # Authenticate
        self.client.force_authenticate(user=self.user)

    def test_get_doctors_list(self):
        """Test retrieving list of doctors"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_doctor_detail(self):
        """Test retrieving doctor details"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['license_number'], 'DOC123456')

    def test_update_doctor(self):
        """Test updating doctor information"""
        data = {
            'consultation_fee': 150.00,
            'bio': 'Updated bio'
        }
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['consultation_fee'], '150.00')
        self.assertEqual(response.data['bio'], 'Updated bio')

    def test_get_doctor_schedules(self):
        """Test retrieving doctor schedules"""
        response = self.client.get(self.schedules_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['day_of_week'], 0)

    def test_get_available_slots(self):
        """Test retrieving available appointment slots"""
        # Test for today
        today = timezone.now().date()
        response = self.client.get(f"{self.available_slots_url}?date={today}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response structure
        self.assertIn('date', response.data)
        self.assertIn('available_slots', response.data)

class DoctorScheduleAPITests(APITestCase):
    def setUp(self):
        # Create test user and doctor
        self.user = User.objects.create_user(
            username='testdoctor',
            email='doctor@example.com',
            password='TestPass123!'
        )
        
        self.doctor = Doctor.objects.create(
            user=self.user,
            specialization='GENERAL',
            license_number='DOC123456',
            phone_number='+1234567890',
            years_of_experience=5,
            consultation_fee=100.00
        )
        
        # URLs
        self.schedule_list_url = reverse('doctorschedule-list')
        
        # Authenticate
        self.client.force_authenticate(user=self.user)

    def test_create_schedule(self):
        """Test creating a new schedule"""
        data = {
            'day_of_week': 1,  # Tuesday
            'start_time': '09:00:00',
            'end_time': '17:00:00',
            'is_available': True
        }
        response = self.client.post(self.schedule_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DoctorSchedule.objects.count(), 1)

    def test_update_schedule(self):
        """Test updating a schedule"""
        # Create a schedule
        schedule = DoctorSchedule.objects.create(
            doctor=self.doctor,
            day_of_week=0,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_available=True
        )
        
        # Update the schedule
        url = reverse('doctorschedule-detail', args=[schedule.id])
        data = {
            'start_time': '10:00:00',
            'end_time': '18:00:00'
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify changes
        schedule.refresh_from_db()
        self.assertEqual(schedule.start_time, time(10, 0))
        self.assertEqual(schedule.end_time, time(18, 0))

    def test_delete_schedule(self):
        """Test deleting a schedule"""
        # Create a schedule
        schedule = DoctorSchedule.objects.create(
            doctor=self.doctor,
            day_of_week=0,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_available=True
        )
        
        # Delete the schedule
        url = reverse('doctorschedule-detail', args=[schedule.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(DoctorSchedule.objects.count(), 0)
