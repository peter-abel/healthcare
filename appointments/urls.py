from django.urls import path
from . import views

urlpatterns = [
    path('book/', views.book_appointment, name='book_appointment'),
    path('book/<int:doctor_id>/', views.book_appointment_with_doctor, name='book_appointment_with_doctor'),
    path('list/', views.appointment_list, name='appointment_list'),
    path('<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('<int:appointment_id>/confirm/', views.confirm_appointment, name='confirm_appointment'),
    path('<int:appointment_id>/complete/', views.complete_appointment, name='complete_appointment'),
    path('<int:appointment_id>/medical-record/', views.create_medical_record, name='create_medical_record'),
    path('medical-records/<int:record_id>/edit/', views.edit_medical_record, name='edit_medical_record'),
]
