"""
MongoDB Models for Employee Management System (EMS) API

These models use MongoDB directly while Django uses SQLite for its internal operations.
"""

from datetime import datetime, timedelta
import random
import string
from bson import ObjectId
from mongodb_handler import mongo_handler
from django.contrib.auth.hashers import make_password, check_password

def get_ist_time():
    """Return the current UTC time plus the IST offset."""
    return datetime.utcnow() + timedelta(hours=5, minutes=30)


class MongoUserManager:
    """Django-like manager for MongoUser"""
    
    def filter(self, **kwargs):
        """Filter users by criteria"""
        collection = mongo_handler.get_collection('users')
        
        # Build filter criteria
        filter_dict = {}
        for key, value in kwargs.items():
            filter_dict[key] = value
        
        # Find matching documents
        cursor = collection.find(filter_dict)
        return MongoUserQuerySet(cursor)
    
    def get(self, **kwargs):
        """Get single user by criteria"""
        results = self.filter(**kwargs)
        if len(results) == 0:
            raise Exception("User not found")
        elif len(results) > 1:
            raise Exception("Multiple users found")
        
        # Access the actual results
        if results._results is None:
            results._results = list(results.cursor)
        
        # Create MongoUser instance from the result
        user_data = results._results[0]
        return MongoUser(**user_data)


class MongoUserQuerySet:
    """Django-like queryset for MongoUser"""
    
    def __init__(self, cursor):
        self.cursor = cursor
        self._results = None
    
    def count(self):
        """Count matching users"""
        if self._results is None:
            self._results = list(self.cursor)
        return len(self._results)
    
    def __len__(self):
        return self.count()
    
    def delete(self):
        """Delete all matching users"""
        if self._results is None:
            self._results = list(self.cursor)
        
        collection = mongo_handler.get_collection('users')
        for result in self._results:
            collection.delete_one({'_id': result['_id']})


class MongoUser:
    """MongoDB User model"""
    
    # Django-like objects manager
    objects = MongoUserManager()
    
    def __init__(self, **kwargs):
        self.collection = mongo_handler.get_collection('users')
        self.data = kwargs
    
    @classmethod
    def create_user(cls, username, email, password, role="employee"):
        """Create a new user"""
        # Clean up unverified users older than 10 minutes before creating new user
        cls.cleanup_unverified_users(email)
        
        user_data = {
            'username': username,
            'email': email,
            'password': make_password(password),
            'is_verified': False,
            'role': role,
            'created_at': get_ist_time(),
            'updated_at': get_ist_time()
        }
        
        collection = mongo_handler.get_collection('users')
        
        # Check if user already exists (only verified users or recent unverified users)
        existing_user = collection.find_one({'email': email})
        if existing_user:
            if existing_user.get('is_verified', False):
                raise ValueError("User with this email already exists and is verified")
            else:
                # User exists but not verified - check if it's recent (within 10 minutes)
                created_at = existing_user.get('created_at')
                if created_at and (get_ist_time() - created_at).total_seconds() < 600:  # 10 minutes
                    raise ValueError("User with this email already exists. Please verify your email or wait 10 minutes to sign up again.")
                else:
                    # Old unverified user - delete and create new
                    collection.delete_one({'email': email, 'is_verified': False})
        
        result = collection.insert_one(user_data)
        user_data['_id'] = result.inserted_id
        return cls(**user_data)
    
    @classmethod
    def cleanup_unverified_users(cls, email=None):
        """Clean up unverified users older than 10 minutes"""
        collection = mongo_handler.get_collection('users')
        ten_minutes_ago = get_ist_time() - timedelta(minutes=10)
        
        query = {
            'is_verified': False,
            'created_at': {'$lt': ten_minutes_ago}
        }
        
        # If email is provided, clean up only for that email
        if email:
            query['email'] = email
            # Also clean up OTPs for this email
            from mongo_models import MongoOTP
            MongoOTP.cleanup_otps_for_email(email)
        
        result = collection.delete_many(query)
        return result.deleted_count
    
    @classmethod 
    def perform_periodic_cleanup(cls):
        """Perform periodic cleanup of unverified users and expired OTPs"""
        from mongo_models import MongoOTP
        
        # Clean up unverified users older than 10 minutes
        users_cleaned = cls.cleanup_unverified_users()
        
        # Clean up expired OTPs
        otps_cleaned = MongoOTP.cleanup_expired_otps()
        
        return {
            'users_cleaned': users_cleaned,
            'otps_cleaned': otps_cleaned
        }
    
    @classmethod
    def get_by_email(cls, email):
        """Get user by email"""
        collection = mongo_handler.get_collection('users')
        user_data = collection.find_one({'email': email})
        return cls(**user_data) if user_data else None
    
    @classmethod
    def get_by_id(cls, user_id):
        """Get user by ID"""
        collection = mongo_handler.get_collection('users')
        user_data = collection.find_one({'_id': ObjectId(user_id)})
        return cls(**user_data) if user_data else None
    
    @classmethod
    def authenticate(cls, email, password):
        """Authenticate user with email and password"""
        user = cls.get_by_email(email)
        if user and user.check_password(password):
            return user
        return None
    
    def check_password(self, password):
        """Check if password is correct"""
        return check_password(password, self.data.get('password'))
    
    def set_password(self, password):
        """Set new password"""
        self.data['password'] = make_password(password)
        self.save()
    
    def verify_email(self):
        """Mark email as verified"""
        self.data['is_verified'] = True
        self.save()
    
    def save(self):
        """Save user data to MongoDB"""
        self.data['updated_at'] = get_ist_time()
        collection = mongo_handler.get_collection('users')
        collection.update_one(
            {'_id': self.data['_id']},
            {'$set': self.data}
        )
    
    @property
    def id(self):
        return str(self.data.get('_id'))
    
    @property
    def username(self):
        return self.data.get('username')
    
    @property
    def email(self):
        return self.data.get('email')
    
    @property
    def password(self):
        return self.data.get('password')
    
    @property
    def is_verified(self):
        return self.data.get('is_verified', False)

    @property
    def role(self):
        return self.data.get('role', 'employee')


class MongoOTPManager:
    """Django-like manager for MongoOTP"""
    
    def filter(self, **kwargs):
        """Filter OTPs by criteria"""
        collection = mongo_handler.get_collection('otps')
        
        # Build filter criteria
        filter_dict = {}
        for key, value in kwargs.items():
            filter_dict[key] = value
        
        # Find matching documents
        cursor = collection.find(filter_dict)
        return MongoOTPQuerySet(cursor)
    
    def get(self, **kwargs):
        """Get single OTP by criteria"""
        results = self.filter(**kwargs)
        if len(results) == 0:
            from django.core.exceptions import ObjectDoesNotExist
            raise ObjectDoesNotExist("OTP matching query does not exist")
        elif len(results) > 1:
            raise Exception("Multiple OTPs found")
        return results[0]


class MongoOTPQuerySet:
    """Django-like queryset for MongoOTP"""
    
    def __init__(self, cursor):
        self.cursor = cursor
        self._results = None
    
    def latest(self, field='created_at'):
        """Get latest OTP by field"""
        if self._results is None:
            self._results = list(self.cursor.sort([(field, -1)]))
        
        if not self._results:
            from django.core.exceptions import ObjectDoesNotExist
            raise ObjectDoesNotExist("OTP matching query does not exist")
        
        return MongoOTP(**self._results[0])
    
    def count(self):
        """Count matching OTPs"""
        if self._results is None:
            self._results = list(self.cursor)
        return len(self._results)
    
    def delete(self):
        """Delete all matching OTPs"""
        if self._results is None:
            self._results = list(self.cursor)
        
        collection = mongo_handler.get_collection('otps')
        deleted_count = 0
        for result in self._results:
            collection.delete_one({'_id': result['_id']})
            deleted_count += 1
        return deleted_count
    
    def __len__(self):
        return self.count()


class MongoOTP:
    """MongoDB OTP model"""
    
    # Django-like objects manager
    objects = MongoOTPManager()
    
    def __init__(self, **kwargs):
        self.collection = mongo_handler.get_collection('otps')
        self.data = kwargs
    
    @classmethod
    def create_otp(cls, email, purpose='signup'):
        """Create a new OTP"""
        # Clean up expired OTPs first (automatic maintenance)
        cls.cleanup_expired_otps()
        
        otp_code = cls.generate_otp()
        otp_data = {
            'email': email,
            'otp': otp_code,
            'purpose': purpose,
            'is_used': False,
            'created_at': get_ist_time()
        }
        
        collection = mongo_handler.get_collection('otps')
        result = collection.insert_one(otp_data)
        otp_data['_id'] = result.inserted_id
        return cls(**otp_data)
    
    @classmethod
    def get_latest_unused(cls, email, purpose):
        """Get latest unused OTP for email and purpose"""
        collection = mongo_handler.get_collection('otps')
        otp_data = collection.find_one(
            {'email': email, 'purpose': purpose, 'is_used': False},
            sort=[('created_at', -1)]
        )
        return cls(**otp_data) if otp_data else None
    
    @staticmethod
    def generate_otp():
        """Generate a 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))
    
    def is_valid(self):
        """Check if OTP is still valid (within 10 minutes)"""
        if self.data.get('is_used'):
            return False
        
        created_at = self.data.get('created_at')
        if not created_at:
            return False
        
        return (get_ist_time() - created_at).total_seconds() < 600  # 10 minutes
    
    def mark_as_used(self):
        """Mark OTP as used"""
        self.data['is_used'] = True
        collection = mongo_handler.get_collection('otps')
        collection.update_one(
            {'_id': self.data['_id']},
            {'$set': {'is_used': True}}
        )
    
    def delete(self):
        """Delete OTP from database (security best practice after verification)"""
        print(f"🗑️ DEBUG: Deleting OTP with ID: {self.data.get('_id')}")
        collection = mongo_handler.get_collection('otps')
        result = collection.delete_one({'_id': self.data['_id']})
        print(f"🗑️ DEBUG: Delete result - Deleted count: {result.deleted_count}")
        return result
    
    @classmethod
    def cleanup_expired_otps(cls, email=None):
        """Delete all expired OTPs (older than 10 minutes)"""
        collection = mongo_handler.get_collection('otps')
        expiry_time = get_ist_time() - timedelta(minutes=10)
        
        query = {'created_at': {'$lt': expiry_time}}
        
        # If email is provided, clean up only for that email
        if email:
            query['email'] = email
            
        result = collection.delete_many(query)
        return result.deleted_count
    
    @classmethod
    def cleanup_otps_for_email(cls, email):
        """Delete all OTPs for a specific email (used when cleaning up unverified users)"""
        collection = mongo_handler.get_collection('otps')
        result = collection.delete_many({'email': email})
        return result.deleted_count
    
    @property
    def otp(self):
        return self.data.get('otp')
    
    @property
    def email(self):
        return self.data.get('email')
    
    @property  
    def purpose(self):
        return self.data.get('purpose')
    
    @property
    def is_used(self):
        return self.data.get('is_used', False)
    
    @property
    def created_at(self):
        return self.data.get('created_at')


class MongoPandit:
    """MongoDB Pandit model"""
    
    def __init__(self, **kwargs):
        self.collection = mongo_handler.get_collection('pandits')
        self.data = kwargs
    
    @classmethod
    def create_pandit(cls, pandit_name, phone, location):
        """Create a new pandit"""
        collection = mongo_handler.get_collection('pandits')
        
        # Check if pandit already exists
        if collection.find_one({'Pandit_name': pandit_name, 'Location': location}):
            raise ValueError("Pandit with this name and location already exists")
        
        pandit_data = {
            'Pandit_name': pandit_name,
            'phone': phone,
            'Location': location,
            'created_at': get_ist_time(),
            'updated_at': get_ist_time()
        }
        
        result = collection.insert_one(pandit_data)
        pandit_data['_id'] = result.inserted_id
        return cls(**pandit_data)
    
    @classmethod
    def get_by_name_and_location(cls, pandit_name, location):
        """Get pandit by name and location"""
        collection = mongo_handler.get_collection('pandits')
        pandit_data = collection.find_one({
            'Pandit_name': pandit_name,
            'Location': location
        })
        return cls(**pandit_data) if pandit_data else None
    
    @classmethod
    def get_all(cls):
        """Get all pandits"""
        collection = mongo_handler.get_collection('pandits')
        pandits = []
        for pandit_data in collection.find():
            pandits.append(cls(**pandit_data))
        return pandits
    
    @classmethod
    def get_by_location(cls, location):
        """Get pandits by location"""
        collection = mongo_handler.get_collection('pandits')
        pandits = []
        for pandit_data in collection.find({'Location': {'$regex': location, '$options': 'i'}}):
            pandits.append(cls(**pandit_data))
        return pandits
    
    def delete(self):
        """Delete pandit"""
        collection = mongo_handler.get_collection('pandits')
        collection.delete_one({'_id': self.data['_id']})
    
    def to_dict(self):
        """Convert to dictionary"""
        data = self.data.copy()
        data['id'] = str(data.pop('_id'))
        return data
    
    @property
    def id(self):
        return str(self.data.get('_id'))
    
    @property
    def pandit_name(self):
        return self.data.get('Pandit_name')
    
    @property
    def phone(self):
        return self.data.get('phone')
    
    @property
    def location(self):
        return self.data.get('Location')


class MongoLoginSession:
    """MongoDB Login Session model"""
    
    def __init__(self, **kwargs):
        self.collection = mongo_handler.get_collection('login_sessions')
        self.data = kwargs
    
    @classmethod
    def create_session(cls, user_id, device_type):
        """Create a new login session"""
        # Fetch username for user_id
        from mongo_models import MongoUser
        user = MongoUser.get_by_id(user_id) if hasattr(MongoUser, 'get_by_id') else None
        username = user.username if user else None
        session_data = {
            'user_id': user_id,
            'username': username,
            'device_type': device_type,
            'login_time': get_ist_time(),
            'is_active': True
        }
        collection = mongo_handler.get_collection('login_sessions')
        result = collection.insert_one(session_data)
        session_data['_id'] = result.inserted_id
        return cls(**session_data)
    
    @classmethod
    def get_latest_login(cls, user_id):
        """Get the latest login session for a user"""
        collection = mongo_handler.get_collection('login_sessions')
        login_data = collection.find_one(
            {'user_id': user_id},
            sort=[('login_time', -1)]
        )
        return cls(**login_data) if login_data else None
    
    @classmethod
    def get_active_session(cls, user_id):
        """Return the latest active login session for a user, or None if not found."""
        collection = mongo_handler.get_collection('login_sessions')
        session = collection.find_one({'user_id': user_id, 'is_active': True}, sort=[('login_time', -1)])
        return cls(**session) if session else None
    
    @property
    def timestamp(self):
        """Return the login_time for session comparison."""
        return self.data.get('login_time')


class MongoLogoutSession:
    """MongoDB Logout Session model"""
    def __init__(self, **kwargs):
        self.collection = mongo_handler.get_collection('logout_sessions')
        self.data = kwargs

    @classmethod
    def create_session(cls, user_id, device_type):
        """Create a new logout session"""
        session_data = {
            'user_id': user_id,
            'device_type': device_type,
            'logout_time': get_ist_time(),
        }
        collection = mongo_handler.get_collection('logout_sessions')
        result = collection.insert_one(session_data)
        session_data['_id'] = result.inserted_id
        return cls(**session_data)

    @classmethod
    def get_latest_logout(cls, user_id):
        """Get the latest logout session for a user"""
        collection = mongo_handler.get_collection('logout_sessions')
        logout_data = collection.find_one(
            {'user_id': user_id},
            sort=[('logout_time', -1)]
        )
        return cls(**logout_data) if logout_data else None

    @classmethod
    def has_logged_out_after(cls, user_id, login_time):
        """Check if user has logged out after a given login time"""
        collection = mongo_handler.get_collection('logout_sessions')
        logout_data = collection.find_one({
            'user_id': user_id,
            'logout_time': {'$gt': login_time}
        })
        return bool(logout_data)


class MongoAttendanceManager:
    """Django-like manager for MongoAttendance"""
    
    def filter(self, **kwargs):
        """Filter attendance records by criteria"""
        collection = mongo_handler.get_collection('attendance')
        
        # Build filter criteria
        filter_dict = {}
        for key, value in kwargs.items():
            filter_dict[key] = value
        
        # Find matching documents
        cursor = collection.find(filter_dict).sort('created_at', -1)  # Sort by latest first
        return MongoAttendanceQuerySet(cursor)
    
    def get(self, **kwargs):
        """Get single attendance record by criteria"""
        results = self.filter(**kwargs)
        if len(results) == 0:
            raise Exception("Attendance record not found")
        elif len(results) > 1:
            raise Exception("Multiple attendance records found")
        
        # Access the actual results
        if results._results is None:
            results._results = list(results.cursor)
        
        # Create MongoAttendance instance from the result
        attendance_data = results._results[0]
        return MongoAttendance(**attendance_data)


class MongoAttendanceQuerySet:
    """Django-like queryset for MongoAttendance"""
    
    def __init__(self, cursor):
        self.cursor = cursor
        self._results = None
    
    def __len__(self):
        """Return count of results"""
        if self._results is None:
            self._results = list(self.cursor)
        return len(self._results)
    
    def __getitem__(self, index):
        """Get item at index"""
        if self._results is None:
            self._results = list(self.cursor)
        
        attendance_data = self._results[index]
        return MongoAttendance(**attendance_data)
    
    def __iter__(self):
        """Iterate over results"""
        if self._results is None:
            self._results = list(self.cursor)
        
        for attendance_data in self._results:
            yield MongoAttendance(**attendance_data)


class MongoAttendance:
    @classmethod
    def get_all_attendance(cls):
        """Return all attendance records as MongoAttendance instances"""
        collection = mongo_handler.get_collection('attendance')
        records = []
        for record_data in collection.find().sort('created_at', -1):
            records.append(cls(**record_data))
        return records
    """MongoDB Attendance model for Employee Management System"""
    
    objects = MongoAttendanceManager()
    
    def __init__(self, **kwargs):
        self.collection = mongo_handler.get_collection('attendance')
        self.data = kwargs
    
    @classmethod
    def punch_in(cls, user_id, date, time, location, latitude, longitude):
        """Record punch in and add to punched_in collection"""
        punched_in_collection = mongo_handler.get_collection('punched_in')
        punched_out_collection = mongo_handler.get_collection('punched_out')
        # Check if user is already punched in
        existing = punched_in_collection.find_one({'user_id': user_id})
        if existing:
            raise ValueError("You have already punched in. Please punch out first.")
        # Get user info
        from mongo_models import MongoUser
        user = MongoUser.get_by_id(user_id)
        punch_in_data = {
            'user_id': user_id,
            'username': user.username if user else None,
            'email': user.email if user else None,
            'punched_in_date': date,
            'punched_in_time': time,
            'location': location,
            'latitude': latitude,
            'longitude': longitude,
            'created_at': get_ist_time()
        }
        punched_in_collection.insert_one(punch_in_data)
        return punch_in_data

    @classmethod
    def punch_out(cls, user_id, date, time, location, latitude, longitude):
        """Record punch out and move from punched_in to punched_out collection"""
        punched_in_collection = mongo_handler.get_collection('punched_in')
        punched_out_collection = mongo_handler.get_collection('punched_out')
        # Find punched in record
        punched_in_record = punched_in_collection.find_one({'user_id': user_id})
        if not punched_in_record:
            raise ValueError("No punch in record found. Please punch in first.")
        punch_out_data = punched_in_record.copy()
        punch_out_data['punched_out_date'] = date
        punch_out_data['punched_out_time'] = time
        punch_out_data['punched_out_location'] = location
        punch_out_data['punched_out_latitude'] = latitude
        punch_out_data['punched_out_longitude'] = longitude
        punch_out_data['punched_out_at'] = get_ist_time()
        punched_out_collection.insert_one(punch_out_data)
        punched_in_collection.delete_one({'user_id': user_id})
        return punch_out_data
    
    @classmethod
    def get_attendance_by_user(cls, user_id, date=None):
        """Get attendance records for a user"""
        collection = mongo_handler.get_collection('attendance')
        query = {'user_id': user_id}
        
        if date:
            query['date'] = date
        
        records = []
        for record_data in collection.find(query).sort('created_at', -1):
            records.append(cls(**record_data))
        return records
    
    @classmethod
    def get_attendance_by_date_range(cls, user_id, start_date, end_date):
        """Get attendance records for a user within date range"""
        collection = mongo_handler.get_collection('attendance')
        query = {
            'user_id': user_id,
            'date': {'$gte': start_date, '$lte': end_date}
        }
        
        records = []
        for record_data in collection.find(query).sort('created_at', -1):
            records.append(cls(**record_data))
        return records
    
    def to_dict(self):
        """Convert to dictionary"""
        data = self.data.copy()
        data['id'] = str(data.pop('_id'))
        return data
    
    @property
    def id(self):
        return str(self.data.get('_id'))
    
    @property
    def user_id(self):
        return self.data.get('user_id')
    
    @property
    def date(self):
        return self.data.get('date')
    
    @property
    def time(self):
        return self.data.get('time')
    
    @property
    def location(self):
        return self.data.get('location')
    
    @property
    def latitude(self):
        return self.data.get('latitude')
    
    @property
    def longitude(self):
        return self.data.get('longitude')
    
    @property
    def action_type(self):
        return self.data.get('action_type')

class MongoLeave:
    """MongoDB Leave model for Employee Management System"""

    def __init__(self, **kwargs):
        self.collection = mongo_handler.get_collection('leaves')
        self.data = kwargs

    @classmethod
    def create_leave(cls, user_id, username, email, leave_type, start_date, end_date, reason, is_full_day):
        """Create a new leave application"""
        leave_data = {
            'user_id': user_id,
            'username': username,
            'email': email,
            'leave_type': leave_type,
            'start_date': start_date,
            'end_date': end_date,
            'reason': reason,
            'is_full_day': is_full_day,
            'status': 'pending',  # Default status
            'created_at': get_ist_time(),
            'updated_at': get_ist_time()
        }
        
        collection = mongo_handler.get_collection('leaves')
        result = collection.insert_one(leave_data)
        leave_data['_id'] = result.inserted_id
        return cls(**leave_data)

    @classmethod
    def get_by_id(cls, leave_id):
        """Get leave by ID"""
        collection = mongo_handler.get_collection('leaves')
        leave_data = collection.find_one({'_id': ObjectId(leave_id)})
        return cls(**leave_data) if leave_data else None
        
    @classmethod
    def get_by_user(cls, user_id):
        """Get all leave applications for a user"""
        collection = mongo_handler.get_collection('leaves')
        leaves = []
        for leave_data in collection.find({'user_id': user_id}).sort('created_at', -1):
            leaves.append(cls(**leave_data))
        return leaves

    @classmethod
    def get_all(cls):
        """Get all leave applications"""
        collection = mongo_handler.get_collection('leaves')
        leaves = []
        for leave_data in collection.find().sort('created_at', -1):
            leaves.append(cls(**leave_data))
        return leaves

    def save(self):
        """Save leave data to MongoDB"""
        self.data['updated_at'] = get_ist_time()
        collection = mongo_handler.get_collection('leaves')
        collection.update_one(
            {'_id': self.data['_id']},
            {'$set': self.data}
        )
    def to_dict(self):
        """Convert to dictionary"""
        data = self.data.copy()
        data['id'] = str(data.pop('_id'))
        # Convert datetime objects to string
        if isinstance(data.get('start_date'), datetime):
            data['start_date'] = data['start_date'].isoformat()
        if isinstance(data.get('end_date'), datetime):
            data['end_date'] = data['end_date'].isoformat()
        if isinstance(data.get('created_at'), datetime):
            data['created_at'] = data['created_at'].isoformat()
        if isinstance(data.get('updated_at'), datetime):
            data['updated_at'] = data['updated_at'].isoformat()
        return data
