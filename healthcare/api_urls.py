from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from patients.api import PatientViewSet, MedicalRecordViewSet
from doctors.api import DoctorViewSet, DoctorScheduleViewSet
from appointments.api import AppointmentViewSet

# Create a schema view for API documentation
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

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'patients', PatientViewSet)
router.register(r'medical-records', MedicalRecordViewSet)
router.register(r'doctors', DoctorViewSet)
router.register(r'doctor-schedules', DoctorScheduleViewSet)
router.register(r'appointments', AppointmentViewSet)

# The API URLs are now determined automatically by the router
urlpatterns = [
    # API documentation
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API endpoints
    path('', include(router.urls)),
    
    # Authentication
    path('auth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]
