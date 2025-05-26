#!/usr/bin/env python
"""
Script to generate API documentation.
"""
import os
import sys
import subprocess
import django
from django.conf import settings

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthcare.settings')
django.setup()

def generate_swagger_json():
    """Generate Swagger JSON file."""
    print("Generating Swagger JSON file...")
    
    # Create output directory if it doesn't exist
    os.makedirs('docs/api', exist_ok=True)
    
    # Generate Swagger JSON
    from drf_yasg.generators import OpenAPISchemaGenerator
    from drf_yasg.views import get_schema_view
    from drf_yasg import openapi
    from rest_framework import permissions
    
    schema_view = get_schema_view(
        openapi.Info(
            title="Healthcare API",
            default_version='v1',
            description="API for managing patients, doctors, appointments, and medical records",
            terms_of_service="https://www.example.com/terms/",
            contact=openapi.Contact(email="contact@example.com"),
            license=openapi.License(name="BSD License"),
        ),
        public=True,
        permission_classes=(permissions.AllowAny,),
    )
    
    # Get the schema
    schema = schema_view.get_schema()
    
    # Write to file
    with open('docs/api/swagger.json', 'w') as f:
        f.write(schema)
    
    print("Swagger JSON file generated in docs/api/swagger.json")

def generate_api_markdown():
    """Generate API documentation in Markdown format."""
    print("Generating API documentation in Markdown format...")
    
    # Create output directory if it doesn't exist
    os.makedirs('docs/api', exist_ok=True)
    
    # Define the API endpoints to document
    endpoints = [
        {
            'name': 'Patients',
            'endpoints': [
                {'method': 'GET', 'path': '/api/v1/patients/', 'description': 'List all patients (doctors only)'},
                {'method': 'POST', 'path': '/api/v1/patients/', 'description': 'Create a new patient'},
                {'method': 'GET', 'path': '/api/v1/patients/{id}/', 'description': 'Get patient details'},
                {'method': 'PUT', 'path': '/api/v1/patients/{id}/', 'description': 'Update patient details'},
                {'method': 'DELETE', 'path': '/api/v1/patients/{id}/', 'description': 'Delete a patient'},
                {'method': 'GET', 'path': '/api/v1/patients/{id}/medical-records/', 'description': 'Get patient\'s medical records'},
            ]
        },
        {
            'name': 'Doctors',
            'endpoints': [
                {'method': 'GET', 'path': '/api/v1/doctors/', 'description': 'List all doctors'},
                {'method': 'POST', 'path': '/api/v1/doctors/', 'description': 'Create a new doctor'},
                {'method': 'GET', 'path': '/api/v1/doctors/{id}/', 'description': 'Get doctor details'},
                {'method': 'PUT', 'path': '/api/v1/doctors/{id}/', 'description': 'Update doctor details'},
                {'method': 'DELETE', 'path': '/api/v1/doctors/{id}/', 'description': 'Delete a doctor'},
                {'method': 'GET', 'path': '/api/v1/doctors/{id}/schedules/', 'description': 'Get doctor\'s schedules'},
                {'method': 'GET', 'path': '/api/v1/doctors/{id}/appointments/', 'description': 'Get doctor\'s appointments'},
                {'method': 'GET', 'path': '/api/v1/doctors/{id}/available-slots/', 'description': 'Get doctor\'s available slots'},
            ]
        },
        {
            'name': 'Appointments',
            'endpoints': [
                {'method': 'GET', 'path': '/api/v1/appointments/', 'description': 'List user\'s appointments'},
                {'method': 'POST', 'path': '/api/v1/appointments/', 'description': 'Create a new appointment'},
                {'method': 'GET', 'path': '/api/v1/appointments/{id}/', 'description': 'Get appointment details'},
                {'method': 'PUT', 'path': '/api/v1/appointments/{id}/', 'description': 'Update appointment details'},
                {'method': 'DELETE', 'path': '/api/v1/appointments/{id}/', 'description': 'Delete an appointment'},
                {'method': 'POST', 'path': '/api/v1/appointments/{id}/confirm/', 'description': 'Confirm an appointment'},
                {'method': 'POST', 'path': '/api/v1/appointments/{id}/complete/', 'description': 'Complete an appointment'},
                {'method': 'POST', 'path': '/api/v1/appointments/{id}/cancel/', 'description': 'Cancel an appointment'},
                {'method': 'GET', 'path': '/api/v1/appointments/upcoming/', 'description': 'Get upcoming appointments'},
                {'method': 'GET', 'path': '/api/v1/appointments/past/', 'description': 'Get past appointments'},
                {'method': 'GET', 'path': '/api/v1/appointments/today/', 'description': 'Get today\'s appointments'},
                {'method': 'GET', 'path': '/api/v1/appointments/analytics/', 'description': 'Get appointment analytics'},
            ]
        },
        {
            'name': 'Medical Records',
            'endpoints': [
                {'method': 'GET', 'path': '/api/v1/medical-records/', 'description': 'List user\'s medical records'},
                {'method': 'POST', 'path': '/api/v1/medical-records/', 'description': 'Create a new medical record'},
                {'method': 'GET', 'path': '/api/v1/medical-records/{id}/', 'description': 'Get medical record details'},
                {'method': 'PUT', 'path': '/api/v1/medical-records/{id}/', 'description': 'Update medical record details'},
                {'method': 'DELETE', 'path': '/api/v1/medical-records/{id}/', 'description': 'Delete a medical record'},
            ]
        },
        {
            'name': 'Authentication',
            'endpoints': [
                {'method': 'POST', 'path': '/api/v1/auth/token/', 'description': 'Get OAuth2 token'},
                {'method': 'POST', 'path': '/api/v1/auth/revoke-token/', 'description': 'Revoke OAuth2 token'},
                {'method': 'POST', 'path': '/api/v1/auth/convert-token/', 'description': 'Convert token'},
            ]
        }
    ]
    
    # Write to file
    with open('docs/api/api.md', 'w') as f:
        f.write('# API Documentation\n\n')
        
        for group in endpoints:
            f.write(f'## {group["name"]}\n\n')
            
            f.write('| Method | Endpoint | Description |\n')
            f.write('| ------ | -------- | ----------- |\n')
            
            for endpoint in group['endpoints']:
                f.write(f'| {endpoint["method"]} | {endpoint["path"]} | {endpoint["description"]} |\n')
            
            f.write('\n')
    
    print("API documentation generated in docs/api/api.md")

def generate_sequence_diagrams():
    """Generate sequence diagrams for key processes."""
    print("Generating sequence diagrams...")
    
    # Create output directory if it doesn't exist
    os.makedirs('docs/diagrams', exist_ok=True)
    
    # Define the sequence diagrams
    diagrams = [
        {
            'name': 'appointment_booking',
            'title': 'Appointment Booking Process',
            'content': '''
sequenceDiagram
    participant Patient
    participant API
    participant Validation
    participant DoctorSchedule
    participant Appointment
    participant Cache
    participant MessageQueue

    Patient->>API: Book Appointment Request
    API->>Validation: Validate Request
    Validation->>DoctorSchedule: Check Availability
    DoctorSchedule->>Validation: Return Available Slots
    Validation->>Appointment: Create Appointment
    Appointment->>Cache: Invalidate Related Caches
    Appointment->>MessageQueue: Schedule Notifications
    API->>Patient: Return Appointment Details
    MessageQueue->>Doctor: Send Notification
    MessageQueue->>Patient: Send Confirmation
'''
        },
        {
            'name': 'medical_record_creation',
            'title': 'Medical Record Creation Process',
            'content': '''
sequenceDiagram
    participant Doctor
    participant API
    participant Authorization
    participant MedicalRecord
    participant Cache
    participant Patient

    Doctor->>API: Create Medical Record Request
    API->>Authorization: Check Permissions
    Authorization->>API: Permissions Granted
    API->>MedicalRecord: Create Medical Record
    MedicalRecord->>Cache: Invalidate Related Caches
    API->>Doctor: Return Medical Record Details
    API->>Patient: Send Notification
'''
        },
        {
            'name': 'authentication',
            'title': 'Authentication Process',
            'content': '''
sequenceDiagram
    participant User
    participant API
    participant OAuth2
    participant JWT
    participant UserDatabase

    User->>API: Login Request
    API->>OAuth2: Validate Credentials
    OAuth2->>UserDatabase: Check User
    UserDatabase->>OAuth2: User Exists
    OAuth2->>JWT: Generate Token
    JWT->>OAuth2: Return Token
    OAuth2->>API: Return Token
    API->>User: Return Token
'''
        }
    ]
    
    # Write to files
    for diagram in diagrams:
        with open(f'docs/diagrams/{diagram["name"]}.md', 'w') as f:
            f.write(f'# {diagram["title"]}\n\n')
            f.write('```mermaid\n')
            f.write(diagram['content'])
            f.write('\n```\n')
    
    print("Sequence diagrams generated in docs/diagrams/ directory")

def main():
    """Main function."""
    # Ensure we're in the project root directory
    if not os.path.exists('manage.py'):
        print("Error: This script must be run from the project root directory.")
        sys.exit(1)
    
    # Generate Swagger JSON
    try:
        generate_swagger_json()
    except Exception as e:
        print(f"Error generating Swagger JSON: {e}")
    
    # Generate API Markdown
    try:
        generate_api_markdown()
    except Exception as e:
        print(f"Error generating API Markdown: {e}")
    
    # Generate sequence diagrams
    try:
        generate_sequence_diagrams()
    except Exception as e:
        print(f"Error generating sequence diagrams: {e}")
    
    print("API documentation generation complete.")

if __name__ == '__main__':
    main()
