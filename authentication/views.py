from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings

# Dynamic model imports based on database configuration
if getattr(settings, 'USE_MONGODB', False):
    from mongo_models import MongoUser as User, MongoOTP as OTP, MongoLoginSession as LoginSession
    print("🌐 DEBUG: Using MongoDB models")
else:
    from .models import User, OTP, LoginSession
    print("🗄️ DEBUG: Using Django models")

from .serializers import (
    UserSignupSerializer, 
    OTPVerificationSerializer, 
    UserLoginSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer
)


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    """User signup endpoint"""
    serializer = UserSignupSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Generate OTP
        otp_code = OTP.generate_otp()
        OTP.objects.create(
            email=user.email,
            otp=otp_code,
            purpose='signup'
        )
        
        # Send OTP via email (console backend for development)
        send_mail(
            'Verify Your Email - PoojaPath',
            f'Your OTP for email verification is: {otp_code}',
            settings.EMAIL_HOST_USER or 'noreply@poojapath.com',
            [user.email],
            fail_silently=False,
        )
        
        return Response({
            'message': 'User created successfully. OTP sent to email.',
            'email': user.email
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """OTP verification endpoint"""
    import sys
    print(f"🚀 DEBUG: verify_otp called!", file=sys.stderr, flush=True)
    print(f"🚀 DEBUG: Request data: {request.data}", file=sys.stderr, flush=True)
    
    serializer = OTPVerificationSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp']
        
        try:
            otp_obj = OTP.objects.filter(
                email=email,
                otp=otp_code,
                is_used=False,
                purpose='signup'
            ).latest('created_at')
            
            print(f"🔍 DEBUG: OTP object type: {type(otp_obj)}")
            print(f"🔍 DEBUG: OTP object has delete method: {hasattr(otp_obj, 'delete')}")
            
            if not otp_obj.is_valid():
                return Response({
                    'error': 'OTP has expired'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            print(f"🔍 DEBUG: About to delete OTP: {otp_obj.otp}")
            print(f"🔍 DEBUG: OTP is_used before delete: {otp_obj.data.get('is_used')}")
            # Delete OTP after successful verification (security best practice)
            delete_result = otp_obj.delete()
            print(f"🔍 DEBUG: OTP delete() method called")
            print(f"🔍 DEBUG: Delete result: {delete_result}")
            
            # Verify it's actually deleted by checking the database
            remaining_count = OTP.objects.filter(email=email, otp=otp_code, purpose='signup').count()
            print(f"🔍 DEBUG: Remaining OTPs with same code: {remaining_count}")
            
            # Mark user as verified
            user = User.objects.get(email=email)
            user.is_verified = True
            user.save()
            
            return Response({
                'message': 'Email verified successfully'
            }, status=status.HTTP_200_OK)
            
        except (OTP.DoesNotExist, Exception):
            return Response({
                'error': 'Invalid OTP'
            }, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """User login endpoint"""
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        device_type = serializer.validated_data['deviceType']
        
        # Create login session
        LoginSession.objects.create(
            user=user,
            device_type=device_type
        )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    """Forgot password endpoint"""
    serializer = ForgotPasswordSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        
        # Generate OTP
        otp_code = OTP.generate_otp()
        OTP.objects.create(
            email=email,
            otp=otp_code,
            purpose='forgot_password'
        )
        
        # Send OTP via email
        send_mail(
            'Reset Your Password - PoojaPath',
            f'Your OTP for password reset is: {otp_code}',
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
    """Reset password with OTP verification"""
    serializer = ResetPasswordSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']
        
        try:
            otp_obj = OTP.objects.filter(
                email=email,
                otp=otp_code,
                is_used=False,
                purpose='forgot_password'
            ).latest('created_at')
            
            if not otp_obj.is_valid():
                return Response({
                    'error': 'OTP has expired'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Delete OTP after successful verification (security best practice)
            otp_obj.delete()
            
            # Update user password
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            
            return Response({
                'message': 'Password reset successfully'
            }, status=status.HTTP_200_OK)
            
        except (OTP.DoesNotExist, Exception):
            return Response({
                'error': 'Invalid OTP'
            }, status=status.HTTP_400_BAD_REQUEST)
        except (User.DoesNotExist, Exception):
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
