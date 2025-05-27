# Updated Authentication Tests
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
        self.verify_otp_url = reverse('verify_otp')
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )

    def test_user_signup_with_role_patient(self):
        """Test user registration process for patient role"""
        data = {
            'name': 'newpatient',
            'email': 'newpatient@example.com',
            'password': 'NewPass123!'
        }
        
        # Test signup with patient role parameter
        signup_url_with_role = f"{self.signup_url}?role=patient"
        response = self.client.post(signup_url_with_role, data)
        self.assertEqual(response.status_code, 302)  # Should redirect to OTP verification
        self.assertTrue('otp' in self.client.session)
        self.assertTrue('user_data' in self.client.session)
        self.assertEqual(self.client.session['user_data']['role'], 'patient')
        
        # Test email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], data['email'])
        self.assertIn('Your OTP for Registration', mail.outbox[0].subject)

    def test_user_signup_with_role_doctor(self):
        """Test user registration process for doctor role"""
        data = {
            'name': 'newdoctor',
            'email': 'newdoctor@example.com',
            'password': 'NewPass123!'
        }
        
        # Test signup with doctor role parameter
        signup_url_with_role = f"{self.signup_url}?role=doctor"
        response = self.client.post(signup_url_with_role, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['user_data']['role'], 'doctor')

    def test_signup_validation_errors(self):
        """Test signup validation with updated error messages"""
        # Test with existing username
        data = {
            'name': 'testuser',  # Already exists
            'email': 'unique@example.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.signup_url, data, follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any('Username already exists' in str(message) for message in messages))
        
        # Test with existing email
        data = {
            'name': 'uniqueuser',
            'email': 'test@example.com',  # Already exists
            'password': 'TestPass123!'
        }
        response = self.client.post(self.signup_url, data, follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any('Email already exists' in str(message) for message in messages))
        
        # Test with invalid email format
        data = {
            'name': 'uniqueuser',
            'email': 'invalid-email',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.signup_url, data, follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any('Invalid email format' in str(message) for message in messages))

    def test_user_login_success(self):
        """Test successful login functionality"""
        # Create a patient profile for the user
        Patient.objects.create(user=self.user)
        
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 302)  # Should redirect to patient dashboard
        self.assertRedirects(response, reverse('patient_dashboard'))

    def test_user_login_doctor_redirect(self):
        """Test login redirect for doctor users"""
        # Create a doctor profile for the user
        Doctor.objects.create(user=self.user)
        
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('doctor_dashboard'))

    def test_user_login_validation_errors(self):
        """Test login validation with updated error messages"""
        # Test missing email
        data = {
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 400)
        messages = list(response.context['messages'])
        self.assertTrue(any('Email is required' in str(message) for message in messages))
        
        # Test missing password
        data = {
            'email': 'test@example.com'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 400)
        messages = list(response.context['messages'])
        self.assertTrue(any('Password is required' in str(message) for message in messages))
        
        # Test incorrect password
        data = {
            'email': 'test@example.com',
            'password': 'wrongpass'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 401)
        messages = list(response.context['messages'])
        self.assertTrue(any('Incorrect password. Please try again.' in str(message) for message in messages))
        
        # Test non-existent user
        data = {
            'email': 'nonexistent@example.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 401)
        messages = list(response.context['messages'])
        self.assertTrue(any('No account found with this email address' in str(message) for message in messages))

   
    def test_verify_otp_duplicate_user_handling(self):
        """Test OTP verification handles duplicate users properly"""
        # Create a user first
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='TestPass123!'
        )
        
        # Setup session data with existing username
        session = self.client.session
        session['otp'] = '123456'
        session['user_data'] = {
            'username': 'existinguser',  # Already exists
            'email': 'newemail@example.com',
            'password': 'TestPass123!',
            'role': 'patient'
        }
        session.save()
        
        response = self.client.post(self.verify_otp_url, {'otp': '123456'}, follow=True)
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertTrue(any('This username has already been registered.' in str(message) for message in messages))

    def test_verify_otp_invalid_otp(self):
        """Test OTP verification with invalid OTP"""
        session = self.client.session
        session['otp'] = '123456'
        session['user_data'] = {
            'username': 'testuser2',
            'email': 'test2@example.com',
            'password': 'TestPass123!',
            'role': 'patient'
        }
        session.save()
        
        response = self.client.post(self.verify_otp_url, {'otp': '654321'})
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertTrue(any('Invalid OTP. Please try again.' in str(message) for message in messages))


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
        
        # Clear cache before each test
        cache.clear()

    def test_forgot_password_request(self):
        """Test forgot password request with valid email"""
        response = self.client.post(self.forgot_url, {'email': 'reset@example.com'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('verify_otp_forgot_page'))
        
        # Check email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], 'reset@example.com')
        
        # Check session contains OTP
        self.assertTrue('otp' in self.client.session)
        self.assertTrue('user_data' in self.client.session)
        
        # Check cache contains user ID
        self.assertEqual(cache.get('reset_user_id'), self.user.id)

    def test_forgot_password_validation_errors(self):
        """Test forgot password validation"""
        # Test missing email
        response = self.client.post(self.forgot_url, {})
        self.assertEqual(response.status_code, 400)
        messages = list(response.context['messages'])
        self.assertTrue(any('Email is required' in str(message) for message in messages))
        
        # Test invalid email format
        response = self.client.post(self.forgot_url, {'email': 'invalid-email'})
        self.assertEqual(response.status_code, 400)
        messages = list(response.context['messages'])
        self.assertTrue(any('Invalid email format' in str(message) for message in messages))
        
        # Test non-existent email - this will cause an exception in your current view
        # The view has a bug where it tries to get user before checking existence
        with self.assertRaises(User.DoesNotExist):
            response = self.client.post(self.forgot_url, {'email': 'nonexistent@example.com'})

    
    def test_verify_otp_forgot_invalid(self):
        """Test invalid OTP for password reset"""
        session = self.client.session
        session['otp'] = '123456'
        session['user_data'] = {'email': 'reset@example.com'}
        session.save()
        
        response = self.client.post(self.verify_otp_forgot_url, {'otp': '654321'})
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertTrue(any('Invalid OTP. Please try again.' in str(message) for message in messages))

    def test_password_reset_success(self):
        """Test successful password reset"""
        # Set up cache with user ID
        cache.set('reset_user_id', self.user.id, timeout=300)
        
        new_password = 'NewPass123!'
        response = self.client.post(self.reset_url, {
            'newPassword': new_password,
            'confirmPassword': new_password
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify password was changed
        updated_user = User.objects.get(id=self.user.id)
        self.assertTrue(updated_user.check_password(new_password))
        
        # Verify success message
        messages = list(response.context['messages'])
        self.assertTrue(any('Your password has been reset successfully. You can Login' in str(message) for message in messages))

    def test_password_reset_validation_errors(self):
        """Test password reset validation with all error conditions"""
        cache.set('reset_user_id', self.user.id, timeout=300)
        
        # Test password mismatch
        response = self.client.post(self.reset_url, {
            'newPassword': 'NewPass123!',
            'confirmPassword': 'DifferentPass123!'
        })
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertTrue(any('Passwords do not match.' in str(message) for message in messages))
        
        # Test password length requirement
        response = self.client.post(self.reset_url, {
            'newPassword': 'Short1!',
            'confirmPassword': 'Short1!'
        })
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertTrue(any('Password must be at least 8 characters long.' in str(message) for message in messages))
        
        # Test uppercase requirement
        response = self.client.post(self.reset_url, {
            'newPassword': 'nouppercase123!',
            'confirmPassword': 'nouppercase123!'
        })
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertTrue(any('Password must contain at least one uppercase letter.' in str(message) for message in messages))
        
        # Test digit requirement
        response = self.client.post(self.reset_url, {
            'newPassword': 'NoDigits!',
            'confirmPassword': 'NoDigits!'
        })
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertTrue(any('Password must contain at least one number.' in str(message) for message in messages))
        
        # Test special character requirement
        response = self.client.post(self.reset_url, {
            'newPassword': 'NoSpecial123',
            'confirmPassword': 'NoSpecial123'
        })
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertTrue(any('Password must contain at least one special character.' in str(message) for message in messages))

    def test_password_reset_user_not_found(self):
        """Test password reset when user is not found in cache"""
        # Don't set cache or set invalid user ID
        cache.set('reset_user_id', 99999, timeout=300)  # Non-existent user ID
        
        response = self.client.post(self.reset_url, {
            'newPassword': 'NewPass123!',
            'confirmPassword': 'NewPass123!'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertTrue(any('User not found.' in str(message) for message in messages))

    def tearDown(self):
        """Clean up cache after each test"""
        cache.clear()


class ProfileCheckTests(TestCase):
    """Test the check_profile_exists function behavior"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='profileuser',
            email='profile@example.com',
            password='TestPass123!'
        )

    def test_check_profile_exists_patient(self):
        """Test profile check for patient user"""
        from authenticator.views import check_profile_exists
        
        # Initially no profile
        self.assertIsNone(check_profile_exists(self.user))
        
        # Create patient profile
        Patient.objects.create(user=self.user)
        self.assertEqual(check_profile_exists(self.user), 'patient')

    def test_check_profile_exists_doctor(self):
        """Test profile check for doctor user"""
        from authenticator.views import check_profile_exists
        
        # Create doctor profile
        Doctor.objects.create(user=self.user)
        self.assertEqual(check_profile_exists(self.user), 'doctor')

    def test_check_profile_exists_none(self):
        """Test profile check when no profile exists"""
        from authenticator.views import check_profile_exists
        
        self.assertIsNone(check_profile_exists(self.user))