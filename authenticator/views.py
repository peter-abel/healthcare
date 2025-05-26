from datetime import date
from urllib.parse import urlencode
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
import random
import string
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.urls import reverse
from doctors.models import Doctor
from patients.models import Patient




# Create your views here.
def sos(request,exception):


    return render(request, "404.html")  




def check_profile_exists(user):
    """
    Check if the user has either a patient or doctor profile.
    Returns the profile type ('patient', 'doctor') or None.
    """
    try:
        if hasattr(user, 'patient'):
            return 'patient'
        elif hasattr(user, 'doctor'):
            return 'doctor'
        return None
    except:
        return None

def user_login(request):
    if request.method == 'POST':
        context = {
            'data': request.POST,
            'has_error': False
        }
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email:
            messages.error(request, 'Email is required')
            context['has_error'] = True

        if not password:
            messages.error(request, 'Password is required')
            context['has_error'] = True

        if context['has_error']:
            return render(request, 'login.html', status=400, context=context)

        # Authenticate using email
        user = authenticate(request, username=email, password=password)

        if user is None:
            user_exist_login = User.objects.filter(email=email).exists()
            if user_exist_login:
                messages.error(request, 'Incorrect password. Please try again.')
            else:
                messages.error(request, 'No account found with this email address')
            return render(request, 'login.html', status=401, context=context)

        login(request, user)

        # Check if user has a profile
        profile_type = check_profile_exists(user)
        if profile_type:
            # Redirect to appropriate dashboard
            if profile_type == 'patient':
                return redirect('patient_dashboard')
            else:
                return redirect('doctor_dashboard')
        else:
            # Redirect to role selection if no profile exists
            return redirect('role_selection')

    return render(request, "login.html")



def generate_otp():
    return ''.join(random.choices(string.digits, k=6))
def signup(request):
    # Get role from query parameter
    role = request.GET.get('role')
    print(f"Debug: Role from URL parameter: {role}")  # Debug line
    
    if role not in ['patient', 'doctor']:
        role = None
        print(f"Debug: Role set to None because it's not valid")  # Debug line
    
    if request.method == 'POST':
        # Also check if role was passed via POST (from hidden form field)
        post_role = request.POST.get('role')
        if post_role and post_role in ['patient', 'doctor']:
            role = post_role
            print(f"Debug: Role from POST data: {role}")  # Debug line
        elif role is None:
            # If no role from URL and no role from POST, this is the issue
            print(f"Debug: No role found in either URL or POST data!")
            
        username = request.POST['name']
        email = request.POST['email']
        password = request.POST['password']
        
        print(f"Debug: Final role being stored in session: {role}")  # Debug line
        
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Invalid email format')
            return redirect('signup')
        
        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('signup')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('signup')
        
        otp = generate_otp()
        request.session['otp'] = otp
        request.session['user_data'] = {
            'username': username,
            'email': email,
            'password': password,
            'role': role  # Store the role in session
        }
        
        # Debug: Print what's being stored in session
        print(f"Debug: Session user_data: {request.session['user_data']}")
        
        # Send OTP via email
        try:
            send_mail(
                'Your OTP for Registration',
                f'Your OTP is: {otp}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            messages.error(request, 'Error sending OTP email. Please try again.')
            return redirect('signup')
        
        return redirect('verify_otp')
    
    # For GET requests, pass the role to the template
    context = {'selected_role': role} if role else {}
    return render(request, 'signup.html', context)


    


def verify_otp(request):
    if request.method == 'POST':
        user_otp = request.POST['otp']
        stored_otp = request.session.get('otp')
        user_data = request.session.get('user_data')
        
        if user_otp == stored_otp:
            # Check if the user already exists
            if User.objects.filter(username=user_data['username']).exists():
                messages.error(request, 'This username has already been registered.')
                return redirect('signup')
            
            if User.objects.filter(email=user_data['email']).exists():
                messages.error(request, 'This email has already been registered.')
                return redirect('signup')
            
            # Try creating the user
            try:
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password']
                )
                user.is_active = True
                user.save()
            except IntegrityError:
                messages.error(request, 'An error occurred during registration. Please try again.')
                return redirect('signup')
            
            # Clear session data after successful registration
            request.session.pop('otp', None)
            #request.session.pop('user_data', None)
            
            # Get the stored role
            stored_role = user_data.get('role')
            print(f"Debug: stored_role = {stored_role}")  # Add this for debugging
            
            if stored_role in ['patient', 'doctor']:
                if stored_role == 'patient':
                    Patient.objects.create(user=user,date_of_birth=date(1900, 1, 1))
                    messages.success(request, 'Registration successful. Please login to complete your patient profile.')
                    request.session.pop('user_data', None)

                    return redirect('patient_profile')
                else:
                    Doctor.objects.create(user=user,years_of_experience=1)
                    messages.success(request, 'Registration successful. Please login to complete your doctor profile.')
                    request.session.pop('user_data', None)

                    return redirect('doctor_profile')
            else:
                messages.success(request, 'Registration successful. Please select your role.')
                return redirect('role_selection')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
     
    return render(request, 'verify_otp.html')

def user_logout(request):
    logout(request)
    return redirect('home') 


@login_required
def role_selection(request):
    """
    View for selecting role (patient or doctor) after signup.
    """
    # Check if user already has a role
    profile_type = check_profile_exists(request.user)
    if profile_type:
        messages.info(request, f"You already have a {profile_type} profile.")
        if profile_type == 'patient':
            return redirect('patient_dashboard')
        else:
            return redirect('doctor_dashboard')

    if request.method == 'POST':
        role = request.POST.get('role')
        if role not in ['patient', 'doctor']:
            messages.error(request, "Invalid role selected.")
            return redirect('role_selection')

        # Create the appropriate profile
        if role == 'patient':
            Patient.objects.create(user=request.user)
            return redirect('patient_profile')
        else:
            Doctor.objects.create(user=request.user)
            return redirect('doctor_profile')

    return render(request, 'choose_role.html')



#Password Reset views.
def forgot(request):
    if request.method == 'POST':
        context = {
            'data': request.POST,
            'has_error': False
        }
        email = request.POST.get('email')

        # Validate email presence and format
        if not email:
            messages.error(request, 'Email is required')
            context['has_error'] = True
        else:
            try:
                validate_email(email)
            except ValidationError:
                messages.error(request, 'Invalid email format')
                context['has_error'] = True

        if context['has_error']:
            return render(request, 'forgot-password.html', status=400, context=context)

        # Check user existence
        user_exists = User.objects.filter(email=email).exists()
        user_reset = User.objects.get(email=email)
        #request.session['reset_user_id'] = user_reset.id
        cache.set('reset_user_id', user_reset.id, timeout=300) 
        if user_exists:
            otp = generate_otp()
            request.session['otp'] = otp
            request.session['user_data'] = {'email': email}

            try:
                send_mail(
                    'Your OTP for Registration',
                    f'Your OTP is: {otp}',
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )
            except Exception as e:
                messages.error(request, f"Error sending OTP email: {str(e)}")
                return redirect('forgot')

            messages.info(request, 'Enter the OTP below.')
            return redirect('verify_otp_forgot_page')
        else:
            messages.error(request, 'No account found with this email address')
            return render(request, 'forgot-password.html', status=401, context=context)

    return render(request, "forgot-password.html")



def verify_otp_forgot_page(request):
    if request.method == 'POST':
        user_otp = request.POST['otp']
        stored_otp = request.session.get('otp')
        #user_data = request.session.get('user_data')

        if user_otp == stored_otp:
            # OTP is correct, store user ID in session for next step
            #request.session['reset_user_id'] = stored_otp
 
            # Clear session data after successful registration
            #del request.session['otp']
            #del request.session['user_data']

            messages.success(request, 'Email confirmed. You can now set a new password.')
            return redirect('reset')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'verify_otp_forgot_page.html')


def reset(request):
    
    
    if request.method == 'POST':
        new_password = request.POST.get('newPassword')
        confirm_password = request.POST.get('confirmPassword')
        
        # Retrieve user
        try:
            reset_user_id = cache.get('reset_user_id')
            user_reset = User.objects.get(id=reset_user_id)

            # Server-side validation
            if new_password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return render(request, "reset-password.html")
            # Password strength validation
            if len(new_password) < 8:
                messages.error(request, "Password must be at least 8 characters long.")
                return render(request, "reset-password.html")

            if not any(char.isupper() for char in new_password):
                messages.error(request, "Password must contain at least one uppercase letter.")
                return render(request, "reset-password.html")

            if not any(char.isdigit() for char in new_password):
                messages.error(request, "Password must contain at least one number.")
                return render(request, "reset-password.html")

            special_chars = "!@#$%^&*(),.?\":{}|<>"
            if not any(char in special_chars for char in new_password):
               messages.error(request, "Password must contain at least one special character.")
               return render(request, "reset-password.html")

            # Set new password
            user_reset.password = make_password(new_password)
            user_reset.save()
            
            # Clear the session
            
            
            messages.success(request, "Your password has been reset successfully. You can Login")
            return redirect('user_login')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('forgot')

       


    return render(request, "reset-password.html")
