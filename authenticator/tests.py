# Fixed Authentication Tests
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail
from django.contrib.auth import get_user_model
from django.core.cache import cache
from patients.models import Patient
from doctors.models import Doctor
import json

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('signup')
        self.login_url = reverse('user_login')
        self.role_selection_url = reverse('role_selection')
        self.verify_otp_url = reverse('verify_otp')
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )

    def test_user_signup(self):
        """Test user registration process"""
        data = {
            'name': 'newuser',
            'email': 'newuser@example.com',
            'password': 'NewPass123!',
            'role': 'patient'
        }
        
        # Test signup form submission
        response = self.client.post(self.signup_url, data)
        self.assertEqual(response.status_code, 302)  # Should redirect to OTP verification
        self.assertTrue('otp' in self.client.session)
        self.assertTrue('user_data' in self.client.session)
        
        # Test email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], data['email'])

    def test_invalid_signup_data(self):
        """Test signup validation"""
        # Test with existing email
        data = {
            'name': 'another',
            'email': 'test@example.com',  # Already exists
            'password': 'TestPass123!'
        }
        response = self.client.post(self.signup_url, data, follow=True)
        # Check for error message in messages framework
        messages = list(response.context['messages'])
        self.assertTrue(any('Email already exists' in str(message) for message in messages))
        
        # Test with invalid email format
        data['email'] = 'invalid-email'
        response = self.client.post(self.signup_url, data, follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any('Invalid email format' in str(message) for message in messages))

    def test_user_login(self):
        """Test login functionality"""
        # Test successful login
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 302)  # Should redirect to dashboard or role selection
        
        # Test invalid credentials
        data['password'] = 'wrongpass'
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 401)
        self.assertContains(response, 'Incorrect password', status_code=401)
        
        # Test non-existent user
        data['email'] = 'nonexistent@example.com'
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 401)
        self.assertContains(response, 'No account found', status_code=401)

    
    def test_verify_otp(self):
        """Test OTP verification"""
        # Setup session data
        session = self.client.session
        session['otp'] = '123456'
        session['user_data'] = {
            'username': 'otpuser',
            'email': 'otp@example.com',
            'password': 'TestPass123!',
            'role': 'patient'
        }
        session.save()
        
        # Test correct OTP
        response = self.client.post(self.verify_otp_url, {'otp': '123456'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='otp@example.com').exists())
        
        # Setup fresh session for incorrect OTP test
        session = self.client.session
        session['otp'] = '123456'
        session['user_data'] = {
            'username': 'otpuser2',
            'email': 'otp2@example.com',
            'password': 'TestPass123!',
            'role': 'patient'
        }
        session.save()
        
        # Test incorrect OTP
        response = self.client.post(self.verify_otp_url, {'otp': '654321'})
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertTrue(any('Invalid OTP' in str(message) for message in messages))

class PasswordResetTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.forgot_url = reverse('forgot')
        self.verify_otp_forgot_url = reverse('verify_otp_forgot_page')
        self.reset_url = reverse('reset')
        
        # Create test user
        self.user = User.objects.create_user(
            username='resetuser',
            email='reset@example.com',
            password='OldPass123!'
        )

    def test_forgot_password_flow(self):
        """Test complete password reset flow"""
        # Request password reset
        response = self.client.post(self.forgot_url, {'email': 'reset@example.com'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        
        # Verify OTP
        session = self.client.session
        otp = session['otp']
        response = self.client.post(self.verify_otp_forgot_url, {'otp': otp})
        self.assertEqual(response.status_code, 302)
        
        # Reset password
        new_password = 'NewPass123!'
        response = self.client.post(self.reset_url, {
            'newPassword': new_password,
            'confirmPassword': new_password
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify new password works
        updated_user = User.objects.get(id=self.user.id)
        self.assertTrue(updated_user.check_password(new_password))

    def test_password_reset_validation(self):
        """Test password reset validation rules"""
        cache.set('reset_user_id', self.user.id, timeout=300)
        
        # Test password mismatch
        response = self.client.post(self.reset_url, {
            'newPassword': 'NewPass123!',
            'confirmPassword': 'DifferentPass123!'
        })
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertTrue(any('Passwords do not match' in str(message) for message in messages))
        
        # Test password strength requirements
        test_cases = [
            ('short1!', 'at least 8 characters'),
            ('nouppercase123!', 'uppercase letter'),
            ('NODIGITS!!', 'number'),
            ('NoSpecial123', 'special character')
        ]
        
        for password, error_msg in test_cases:
            response = self.client.post(self.reset_url, {
                'newPassword': password,
                'confirmPassword': password
            })
            self.assertEqual(response.status_code, 200)
            messages = list(response.context['messages'])
            self.assertTrue(any(error_msg in str(message) for message in messages))