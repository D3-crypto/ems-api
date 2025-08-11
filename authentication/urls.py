from django.urls import path
from . import views_mongo as views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('login/', views.login, name='login'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('punch-in/', views.punch_in, name='punch_in'),
    path('punch-out/', views.punch_out, name='punch_out'),
    path('attendance/', views.get_attendance, name='get_attendance'),
    path('attendance/status/', views.get_attendance_status, name='get_attendance_status'),
    path('logout/', views.logout, name='logout'),
]
