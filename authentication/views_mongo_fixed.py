from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from decouple import config
from mongo_models import MongoUser, MongoOTP, MongoLoginSession
from .serializers import (
    UserSignupSerializer, 
    OTPVerificationSerializer, 
    UserLoginSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer
)


def generate_jwt_tokens(mongo_user):
    """Generate JWT tokens for MongoDB user using Django User"""
    # Get or create corresponding Django user
    django_user, created = User.objects.get_or_create(
        username=mongo_user.email,  # Use email as username for uniqueness
        defaults={
            'email': mongo_user.email,
            'is_active': True
        }
    )
    
    refresh = RefreshToken.for_user(django_user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    """User signup endpoint using MongoDB"""
    serializer = UserSignupSerializer(data=request.data)
    if serializer.is_valid():
        try:
            # Create user in MongoDB
            user = MongoUser.create_user(
                username=serializer.validated_data['user_name'],
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            
            # Generate OTP
            otp_obj = MongoOTP.create_otp(
                email=user.email,
                purpose='signup'
            )
            
            # Send OTP via email
            send_mail(
                'Verify Your Email - PoojaPath',
                f'Your OTP for email verification is: {otp_obj.otp}',
                settings.EMAIL_HOST_USER or 'noreply@poojapath.com',
                [user.email],
                fail_silently=False,
            )
            
            return Response({
                'message': 'User created successfully. Please verify your email.',
                'user_id': user.id
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """OTP verification endpoint using MongoDB"""
    import sys
    print(f"🚀 DEBUG: verify_otp called!", file=sys.stderr, flush=True)
    print(f"🚀 DEBUG: Request data: {request.data}", file=sys.stderr, flush=True)
    
    serializer = OTPVerificationSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp']
        
        # Get the latest unused OTP
        otp_obj = MongoOTP.get_latest_unused(email, 'signup')
        
        if not otp_obj:
            return Response({
                'error': 'Invalid OTP'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if otp_obj.otp != otp_code:
            return Response({
                'error': 'Invalid OTP'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not otp_obj.is_valid():
            return Response({
                'error': 'OTP has expired'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Delete OTP after successful verification (security best practice)
        otp_obj.delete()
        
        # Mark user as verified
        user = MongoUser.get_by_email(email)
        if user:
            user.verify_email()
            
            return Response({
                'message': 'Email verified successfully'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """User login endpoint using MongoDB"""
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        device_type = serializer.validated_data.get('device_type', 'web')
        
        # Authenticate user with MongoDB
        user = MongoUser.authenticate(email, password)
        
        if user and user.is_verified:
            # Create login session
            session = MongoLoginSession.create_session(
                user_id=user.id,
                device_type=device_type
            )
            
            # Generate JWT tokens
            tokens = generate_jwt_tokens(user)
            
            return Response({
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                },
                'tokens': tokens
            }, status=status.HTTP_200_OK)
        
        elif user and not user.is_verified:
            return Response({
                'error': 'Please verify your email before logging in'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        else:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    """Forgot password endpoint using MongoDB"""
    print(f"🔍 DEBUG: Forgot password called for email: {request.data.get('email')}")
    
    serializer = ForgotPasswordSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        print(f"🔍 DEBUG: Looking up user with email: {email}")
        
        # Check if user exists
        user = MongoUser.get_by_email(email)
        print(f"🔍 DEBUG: User lookup result: {user}")
        if user:
            print(f"🔍 DEBUG: User data: {user.data}")
        
        if not user:
            print(f"🔍 DEBUG: User not found, returning 404")
            return Response({
                'error': 'User with this email does not exist'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Generate OTP
        otp_obj = MongoOTP.create_otp(
            email=email,
            purpose='forgot_password'
        )
        
        # Send OTP via email
        send_mail(
            'Reset Your Password - PoojaPath',
            f'Your OTP for password reset is: {otp_obj.otp}',
            settings.EMAIL_HOST_USER or 'noreply@poojapath.com',
            [email],
            fail_silently=False,
        )
        
        return Response({
            'message': 'OTP sent to email for password reset'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """Reset password endpoint using MongoDB"""
    serializer = ResetPasswordSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']
        
        # Get the latest unused OTP for forgot password
        otp_obj = MongoOTP.get_latest_unused(email, 'forgot_password')
        
        if not otp_obj:
            return Response({
                'error': 'Invalid OTP'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if otp_obj.otp != otp_code:
            return Response({
                'error': 'Invalid OTP'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not otp_obj.is_valid():
            return Response({
                'error': 'OTP has expired'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Delete OTP after successful verification (security best practice)
        otp_obj.delete()
        
        # Update user password
        user = MongoUser.get_by_email(email)
        if user:
            user.set_password(new_password)
            
            return Response({
                'message': 'Password reset successfully'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
