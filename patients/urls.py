from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='patient_dashboard'),
    path('profile/', views.profile, name='patient_profile'),
    path('medical-records/', views.medical_records_list, name='medical_records_list'),
    path('medical-records/<int:record_id>/', views.medical_record_detail, name='medical_record_detail'),
]
