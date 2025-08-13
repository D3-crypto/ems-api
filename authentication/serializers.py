from rest_framework import serializers
from django.contrib.auth import authenticate
from django.conf import settings

# Dynamic model imports based on database configuration
if getattr(settings, 'USE_MONGODB', False):
    from mongo_models import MongoUser as User, MongoOTP as OTP, MongoAttendance as Attendance, MongoLeave
else:
    from .models import User, OTP, Attendance


class UserSignupSerializer(serializers.Serializer):
    user_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    reEnterPassword = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['password'] != data['reEnterPassword']:
            raise serializers.ValidationError("Passwords do not match")
        
        # Check using appropriate model (MongoDB or Django ORM)
        if getattr(settings, 'USE_MONGODB', False):
            # For MongoDB, we'll let the model handle cleanup and validation
            # The MongoUser.create_user method now handles unverified user cleanup
            pass
        else:
            if User.objects.filter(email=data['email']).exists():
                raise serializers.ValidationError("User with this email already exists")
        
        return data

    def create(self, validated_data):
        validated_data.pop('reEnterPassword')
        user = User.objects.create_user(
            username=validated_data['user_name'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    deviceType = serializers.CharField()

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError("Invalid email or password")
            if not user.is_verified:
                raise serializers.ValidationError("Email not verified")
            data['user'] = user
        else:
            raise serializers.ValidationError("Email and password required")

        return data


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        # Check using appropriate model (MongoDB or Django ORM)
        if getattr(settings, 'USE_MONGODB', False):
            if not User.get_by_email(value):
                raise serializers.ValidationError("User with this email does not exist")
        else:
            if not User.objects.filter(email=value).exists():
                raise serializers.ValidationError("User with this email does not exist")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data


class PunchInSerializer(serializers.Serializer):
    date = serializers.CharField(max_length=20)
    time = serializers.CharField(max_length=20)
    location = serializers.CharField(max_length=255)
    latitude = serializers.CharField(max_length=50)
    longitude = serializers.CharField(max_length=50)

    def validate(self, data):
        # Basic validation for required fields
        if not all([data.get('date'), data.get('time'), data.get('location'), 
                   data.get('latitude'), data.get('longitude')]):
            raise serializers.ValidationError("All fields are required: date, time, location, latitude, longitude")
        return data


class PunchOutSerializer(serializers.Serializer):
    date = serializers.CharField(max_length=20)
    time = serializers.CharField(max_length=20)
    location = serializers.CharField(max_length=255)
    latitude = serializers.CharField(max_length=50)
    longitude = serializers.CharField(max_length=50)

    def validate(self, data):
        # Basic validation for required fields
        if not all([data.get('date'), data.get('time'), data.get('location'), 
                   data.get('latitude'), data.get('longitude')]):
            raise serializers.ValidationError("All fields are required: date, time, location, latitude, longitude")
        return data


class AttendanceSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    user_id = serializers.CharField(read_only=True)
    date = serializers.CharField()
    time = serializers.CharField()
    location = serializers.CharField()
    latitude = serializers.CharField()
    longitude = serializers.CharField()
    action_type = serializers.CharField()
    created_at = serializers.DateTimeField(read_only=True)


class LeaveSerializer(serializers.Serializer):
    leave_type = serializers.CharField(max_length=100)
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    reason = serializers.CharField(max_length=500)
    is_full_day = serializers.BooleanField()

    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("End date must be after start date.")
        return data

class LeaveListSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    user_id = serializers.CharField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    leave_type = serializers.CharField(read_only=True)
    start_date = serializers.DateTimeField(read_only=True)
    end_date = serializers.DateTimeField(read_only=True)
    reason = serializers.CharField(read_only=True)
    is_full_day = serializers.BooleanField(read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
