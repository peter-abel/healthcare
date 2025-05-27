from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from datetime import time, timedelta, date
from django.db import IntegrityError
from django.core.cache import cache
from unittest.mock import patch, MagicMock

from .models import Doctor, DoctorSchedule
from .serializers import DoctorSerializer, DoctorCreateSerializer, DoctorScheduleSerializer


class DoctorModelTests(TestCase):
    """Test Doctor model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testdoctor',
            email='doctor@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe'
        )
        
        self.doctor_data = {
            'user': self.user,
            'specialization': 'GENERAL',
            'license_number': 'DOC123456',
            'phone_number': '+1234567890',
            'years_of_experience': 5,
            'consultation_fee': 100.00,
            'bio': 'Experienced general practitioner'
        }
    
    def test_doctor_creation(self):
        """Test successful doctor creation"""
        doctor = Doctor.objects.create(**self.doctor_data)
        self.assertEqual(doctor.user, self.user)
        self.assertEqual(doctor.specialization, 'GENERAL')
        self.assertEqual(str(doctor), "Dr. John Doe - General Practice")
    
    def test_doctor_unique_license(self):
        """Test that license numbers must be unique"""
        Doctor.objects.create(**self.doctor_data)
        
        # Create another user with same license
        user2 = User.objects.create_user(username='doctor2', email='doc2@test.com')
        doctor_data_2 = self.doctor_data.copy()
        doctor_data_2['user'] = user2
        
        with self.assertRaises(IntegrityError):
            Doctor.objects.create(**doctor_data_2)
    
    def test_doctor_phone_validation(self):
        """Test phone number validation"""
        invalid_data = self.doctor_data.copy()
        invalid_data['phone_number'] = 'invalid-phone'
        
        doctor = Doctor(**invalid_data)
        with self.assertRaises(ValidationError):
            doctor.full_clean()


class DoctorScheduleModelTests(TestCase):
    """Test DoctorSchedule model functionality"""
    
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
    
    def test_schedule_creation(self):
        """Test schedule creation and string representation"""
        schedule = DoctorSchedule.objects.create(
            doctor=self.doctor,
            day_of_week=0,  # Monday
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_available=True
        )
        
        expected_str = f"{self.doctor} - Monday 09:00:00-17:00:00"
        self.assertEqual(str(schedule), expected_str)
    
    def test_schedule_time_validation(self):
        """Test that end time must be after start time"""
        with self.assertRaises(ValidationError):
            schedule = DoctorSchedule(
                doctor=self.doctor,
                day_of_week=1,
                start_time=time(17, 0),  # 5:00 PM
                end_time=time(9, 0),     # 9:00 AM
                is_available=True
            )
            schedule.full_clean()


class DoctorSerializerTests(TestCase):
    """Test Doctor serializers"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testdoctor',
            email='doctor@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe'
        )
        
        self.doctor = Doctor.objects.create(
            user=self.user,
            specialization='GENERAL',
            license_number='DOC123456',
            phone_number='+1234567890',
            years_of_experience=5,
            consultation_fee=100.00
        )
    
    def test_doctor_serializer(self):
        """Test DoctorSerializer output"""
        serializer = DoctorSerializer(instance=self.doctor)
        data = serializer.data
        
        self.assertEqual(data['id'], self.doctor.id)
        self.assertEqual(data['user']['username'], 'testdoctor')
        self.assertEqual(data['specialization'], 'GENERAL')
        self.assertEqual(data['license_number'], 'DOC123456')
    
    def test_doctor_create_serializer(self):
        """Test DoctorCreateSerializer validation"""
        user2 = User.objects.create_user(username='doctor2', email='doc2@test.com')
        
        data = {
            'user': user2.id,
            'specialization': 'CARDIO',
            'license_number': 'DOC789012',
            'phone_number': '+1987654321',
            'years_of_experience': 3,
            'consultation_fee': 150.00
        }
        
        serializer = DoctorCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Test validation for user with existing doctor profile
        data['user'] = self.user.id  # User already has doctor profile
        serializer = DoctorCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('user', serializer.errors)