from django.conf import settings
from django.contrib.auth.models import AbstractUser
import random
import string
from datetime import datetime, timedelta
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'


class OTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    purpose = models.CharField(max_length=20, choices=[
        ('signup', 'Signup'),
        ('forgot_password', 'Forgot Password'),
    ])

    class Meta:
        db_table = 'otps'

    def is_valid(self):
        """Check if OTP is still valid (within 10 minutes)"""
        return (datetime.now() - self.created_at.replace(tzinfo=None)).seconds < 600

    @staticmethod
    def generate_otp():
        """Generate a 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))


class LoginSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device_type = models.CharField(max_length=50)
    login_time = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'login_sessions'


class Attendance(models.Model):
    """Model for employee punch in/out attendance tracking"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.CharField(max_length=20)  # Date in string format
    time = models.CharField(max_length=20)  # Time in string format
    location = models.CharField(max_length=255)  # Location name
    latitude = models.CharField(max_length=50)  # Latitude as string
    longitude = models.CharField(max_length=50)  # Longitude as string
    action_type = models.CharField(max_length=10, choices=[
        ('punch_in', 'Punch In'),
        ('punch_out', 'Punch Out'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'attendance'
        ordering = ['-created_at']
