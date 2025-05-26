from django.urls import path
from . import views

urlpatterns = [
    path('doctor-dashboard/', views.dashboard, name='doctor_dashboard'),
    path('doctor-profile/', views.profile, name='doctor_profile'),
    path('schedule/', views.manage_schedule, name='manage_schedule'),
    path('appointments/', views.appointments_list, name='doctor_appointments'),
    path('search/', views.doctor_search, name='doctor_search'),
    path('<int:doctor_id>/', views.doctor_detail, name='doctor_detail'),
]
