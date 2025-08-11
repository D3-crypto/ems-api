from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from decouple import config
from mongo_models import MongoUser, MongoOTP, MongoLoginSession, MongoAttendance, MongoLogoutSession
from mongodb_handler import mongo_handler
from .serializers import (
    UserSignupSerializer, 
    OTPVerificationSerializer, 
    UserLoginSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    PunchInSerializer,
    PunchOutSerializer,
    AttendanceSerializer
)


def generate_jwt_tokens(mongo_user):
    """Generate JWT tokens for MongoDB user using Django User"""
    User = get_user_model()
    
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
                'Verify Your Email - Employee Management System',
                f'Your OTP for email verification is: {otp_obj.otp}',
                settings.EMAIL_HOST_USER or 'noreply@ems.com',
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
    email = request.data.get('email')
    password = request.data.get('password') 
    device_type = request.data.get('deviceType', 'web')
    
    if not email or not password:
        return Response({
            'error': 'Email and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Authenticate user with MongoDB
    user = MongoUser.authenticate(email, password)
    
    if user and user.is_verified:
        # Log out all previous sessions for this user
        from mongo_models import MongoLoginSession, MongoLogoutSession
        collection = MongoLoginSession().collection
        # Find all active sessions for user
        active_sessions = collection.find({'user_id': user.id, 'is_active': True})
        for session in active_sessions:
            # Mark session as inactive and create a logout session
            collection.update_one({'_id': session['_id']}, {'$set': {'is_active': False}})
            MongoLogoutSession.create_session(user.id, device_type)

        # Create new login session
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
            'Reset Your Password - Employee Management System',
            f'Your OTP for password reset is: {otp_obj.otp}',
            settings.EMAIL_HOST_USER or 'noreply@ems.com',
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
        # ENFORCEMENT: Check if user has logged out after last login
        user = MongoUser.get_by_email(email)
        if user:
            latest_logout = MongoLogoutSession.get_latest_logout(user.id)
            latest_login = MongoLoginSession.get_latest_login(user.id)
            if latest_logout and latest_login and latest_logout.data['logout_time'] > latest_login.timestamp:
                return Response({'error': 'You have logged out. Please log in again to reset password.'}, status=status.HTTP_401_UNAUTHORIZED)
        # Get the latest unused OTP for forgot password
        otp_obj = MongoOTP.get_latest_unused(email, 'forgot_password')
        if not otp_obj:
            return Response({
                'error': 'Invalid OTP'
            }, status=status.HTTP_400_BAD_REQUEST)
        if otp_obj.otp != otp_code:
            return Response({'error': 'Incorrect OTP'}, status=status.HTTP_400_BAD_REQUEST)
        
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


def get_user_id_from_request(request):
    """Helper function to get MongoDB user ID from JWT token"""
    django_user = request.user
    if django_user and hasattr(django_user, 'email'):
        mongo_user = MongoUser.get_by_email(django_user.email)
        if mongo_user:
            return mongo_user.id
    return None


@api_view(['POST'])
def punch_in(request):
    """Employee punch in endpoint using MongoDB"""
    location = request.data.get('location')
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    # Get user info from request.user
    django_user = getattr(request, 'user', None)
    if not django_user or not django_user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    from mongo_models import MongoUser
    user = MongoUser.get_by_email(django_user.email)
    if not user:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    user_id = user.id
    username = user.username
    email = user.email
    from datetime import datetime
    date = datetime.now().strftime('%Y-%m-%d')
    time = datetime.now().strftime('%H:%M:%S')
    # ENFORCEMENT: Check if user is already punched in
    from mongo_models import mongo_handler
    punched_in_collection = mongo_handler.get_collection('punched_in')
    existing = punched_in_collection.find_one({'user_id': user_id})
    if existing:
        return Response({'error': 'You have already punched in. Please punch out first.'}, status=status.HTTP_400_BAD_REQUEST)
    # ENFORCEMENT: Check if user is logged in (active session)
    login_sessions = mongo_handler.get_collection('login_sessions')
    active_session = login_sessions.find_one({'user_id': user_id, 'is_active': True})
    if not active_session:
        return Response({'error': 'User is not logged in. Please log in again.'}, status=status.HTTP_401_UNAUTHORIZED)
    # ENFORCEMENT: Prevent duplicate punch in for same user on same day
    today_punch_in = punched_in_collection.find_one({'user_id': user_id, 'punched_in_date': date})
    if today_punch_in:
        return Response({'error': 'You have already punched in today. Please punch out before punching in again.'}, status=status.HTTP_400_BAD_REQUEST)
    # Record punch in
    punch_in_data = {
        'user_id': user_id,
        'username': username,
        'email': email,
        'punched_in_date': date,
        'punched_in_time': time,
        'location': location,
        'latitude': latitude,
        'longitude': longitude,
        'created_at': datetime.utcnow()
    }
    result = punched_in_collection.insert_one(punch_in_data)
    # Also insert into attendance collection
    attendance_collection = mongo_handler.get_collection('attendance')
    attendance_doc = punch_in_data.copy()
    attendance_collection.insert_one(attendance_doc)
    # Add the inserted _id to the response and serialize ObjectId/datetime fields
    punch_in_data['_id'] = str(result.inserted_id)
    if 'created_at' in punch_in_data:
        punch_in_data['created_at'] = str(punch_in_data['created_at'])
    return Response({'message': 'Punch in successful', 'data': punch_in_data}, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def punch_out(request):
    """Employee punch out endpoint using MongoDB"""
    location = request.data.get('location')
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    # Get user info from request.user
    django_user = getattr(request, 'user', None)
    if not django_user or not django_user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    from mongo_models import MongoUser, MongoLoginSession
    user = MongoUser.get_by_email(django_user.email)
    if not user:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    user_id = user.id
    username = user.username
    email = user.email
    # ENFORCEMENT: Check if user has an active session (must be logged in)
    active_session = MongoLoginSession.get_active_session(user_id)
    if not active_session:
        return Response({'error': 'No active session found. Please login first.'}, status=status.HTTP_401_UNAUTHORIZED)
    from datetime import datetime
    date = datetime.now().strftime('%Y-%m-%d')
    time = datetime.now().strftime('%H:%M:%S')
    # ENFORCEMENT: Check if user is punched in
    from mongo_models import mongo_handler, MongoAttendance
    punched_in_collection = mongo_handler.get_collection('punched_in')
    punched_in_record = punched_in_collection.find_one({'user_id': user_id})
    if not punched_in_record:
        return Response({'error': 'No punch in record found. Please punch in first.'}, status=status.HTTP_400_BAD_REQUEST)
    # Record punch out
    punch_out_data = MongoAttendance.punch_out(
        user_id=user_id,
        date=date,
        time=time,
        location=location,
        latitude=latitude,
        longitude=longitude
    )
    # Update punch-out details in attendance collection
    attendance_collection = mongo_handler.get_collection('attendance')
    attendance_collection.update_one(
        {'user_id': user_id, 'punched_out_date': {'$exists': False}},
        {'$set': {
            'punched_out_date': date,
            'punched_out_time': time,
            'punched_out_location': location,
            'punched_out_latitude': latitude,
            'punched_out_longitude': longitude,
            'punched_out_at': datetime.utcnow()
        }}
    )
    # Serialize ObjectId and datetime fields for JSON response
    if punch_out_data:
        punch_out_data["_id"] = str(punch_out_data["_id"])
        if "created_at" in punch_out_data:
            punch_out_data["created_at"] = punch_out_data["created_at"].isoformat() if punch_out_data["created_at"] else None
        if "punched_out_at" in punch_out_data:
            punch_out_data["punched_out_at"] = punch_out_data["punched_out_at"].isoformat() if punch_out_data["punched_out_at"] else None
    return Response({"message": "Punch out successful", "data": punch_out_data}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """User logout endpoint using MongoDB"""
    user_id = get_user_id_from_request(request)
    device_type = request.data.get('deviceType', 'web')
    if not user_id:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    # Create logout session
    MongoLogoutSession.create_session(user_id=user_id, device_type=device_type)

    # Mark login session as inactive (optional, if you want to track)
    collection = mongo_handler.get_collection('login_sessions')
    collection.update_many({'user_id': user_id, 'is_active': True}, {'$set': {'is_active': False}})

    return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_attendance(request):
    """Get attendance records for all users"""
    try:

        # Get all attendance records for all users
        records = MongoAttendance.get_all_attendance()
        attendance_data = []
        for record in records:
            rec_dict = record.to_dict()
            if 'punch_in_id' in rec_dict:
                rec_dict['punch_in_id'] = str(rec_dict['punch_in_id'])
            if 'punch_out_id' in rec_dict:
                rec_dict['punch_out_id'] = str(rec_dict['punch_out_id'])
            attendance_data.append(rec_dict)
        return Response({
            'message': 'Attendance records retrieved successfully',
            'count': len(attendance_data),
            'data': attendance_data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': f'Error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_attendance_status(request):
    """Get attendance status for a specific user by email"""
    try:
        # Implement attendance status logic here
        # Example: return Response({'status': 'ok'}, status=status.HTTP_200_OK)
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'An error occurred while checking attendance status'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
