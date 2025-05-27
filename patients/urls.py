from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='patient_dashboard'),
    path('profile/', views.profile, name='patient_profile'),
]
