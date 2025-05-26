from django.urls import path
from . import views

urlpatterns = [
    
    path('login/',views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='logout'), 
    path('verify_otp/',views.verify_otp, name='verify_otp'),
    path('reset/',views.reset, name='reset' ),
    path('404/',views.sos, name='sos'),
    path('signup/',views.signup, name='signup' ),
    path('forgot/',views.forgot, name='forgot' ),
    path('forgot_page/',views.verify_otp_forgot_page, name='verify_otp_forgot_page' ),
    path('role-selection/', views.role_selection, name='role_selection'),
]
