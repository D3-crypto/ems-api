# Employee Management System (EMS) API Documentation

## Overview
This is an Employee Management System API built with Django and Django REST Framework. It provides employee authentication, attendance tracking with punch in/out functionality, and user management features.

## Features
- 🔐 Employee Registration & Authentication
- ✉️ OTP-based Email Verification
- 🔑 JWT Token-based Authentication
- 📍 Punch In/Out with Location Tracking
- 📊 Attendance Records Management
- 🔒 Password Reset Functionality
- 🗄️ MongoDB Integration
- 🧑‍💼 Pandit Management (Legacy feature retained)

## Technology Stack
- Django 5.2
- Django REST Framework
- MongoDB (Primary Database)
- SQLite (Django Internal Operations)
- JWT Authentication
- Python 3.10+

## API Endpoints

### Base URL
```
http://localhost:8000/api/employee/
```

### Authentication Endpoints

#### 1. Employee Signup
**POST** `/signup/` (No auth required)

Register a new employee account.

```json
{
  "user_name": "john_doe",
  "email": "john@company.com",
  "password": "SecurePassword123",
  "reEnterPassword": "SecurePassword123"
}
```

**Response:**
```json
{
  "message": "User created successfully. Please verify your email.",
  "user_id": "64f7b1234567890abcdef123"
}
```

#### 2. OTP Verification
**POST** `/verify-otp/` (No auth required)

Verify the OTP sent to employee's email after signup.

```json
{
  "email": "john@company.com",
  "otp": "123456"
}
```

**Response:**
```json
{
  "message": "Email verified successfully",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### 3. Employee Login
**POST** `/login/` (No auth required)

Authenticate an employee and get access tokens.

```json
{
  "email": "john@company.com",
  "password": "SecurePassword123",
  "deviceType": "mobile"
}
```

**Response:**
```json
{
  "message": "Login successful",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user_id": "64f7b1234567890abcdef123"
}
```

#### 4. Forgot Password
**POST** `/forgot-password/` (No auth required)

Request OTP for password reset.

```json
{
  "email": "john@company.com"
}
```

**Response:**
```json
{
  "message": "OTP sent to email for password reset"
}
```

#### 5. Reset Password
**POST** `/reset-password/` (**Requires Authorization header**)

Reset password using OTP.

```json
{
  "email": "john@company.com",
  "otp": "123456",
  "new_password": "NewSecurePassword123",
  "confirm_password": "NewSecurePassword123"
}
```

**Response:**
```json
{
  "message": "Password reset successfully"
}
```

### Attendance Endpoints (Requires Authentication)

#### 6. Punch In
**POST** `/punch-in/` (**Requires Authorization header**)

Record employee punch in with location data.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "date": "2025-08-11",
  "time": "09:00:00",
  "location": "Office Building, Mumbai",
  "latitude": "19.0760",
  "longitude": "72.8777"
}
```

**Response:**
```json
{
  "message": "Punch in successful",
  "attendance_id": "64f7b1234567890abcdef456",
  "data": {
    "id": "64f7b1234567890abcdef456",
    "user_id": "64f7b1234567890abcdef123",
    "date": "2025-08-11",
    "time": "09:00:00",
    "location": "Office Building, Mumbai",
    "latitude": "19.0760",
    "longitude": "72.8777",
    "action_type": "punch_in"
  }
}
```

#### 7. Punch Out
**POST** `/punch-out/` (**Requires Authorization header**)

Record employee punch out with location data.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "date": "2025-08-11",
  "time": "18:00:00",
  "location": "Office Building, Mumbai",
  "latitude": "19.0760",
  "longitude": "72.8777"
}
```

**Response:**
```json
{
  "message": "Punch out successful",
  "attendance_id": "64f7b1234567890abcdef789",
  "data": {
    "id": "64f7b1234567890abcdef789",
    "user_id": "64f7b1234567890abcdef123",
    "date": "2025-08-11",
    "time": "18:00:00",
    "location": "Office Building, Mumbai",
    "latitude": "19.0760",
    "longitude": "72.8777",
    "action_type": "punch_out"
  }
}
```

#### 8. Get Attendance Records
**GET** `/attendance/` (**Requires Authorization header**)

Retrieve employee attendance records.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `date` (optional): Get records for specific date (YYYY-MM-DD)
- `start_date` & `end_date` (optional): Get records for date range

**Examples:**
- Get all records: `/attendance/`
- Get today's records: `/attendance/?date=2025-08-11`
- Get range: `/attendance/?start_date=2025-08-01&end_date=2025-08-31`

**Response:**
```json
{
  "message": "Attendance records retrieved successfully",
  "count": 2,
  "data": [
    {
      "id": "64f7b1234567890abcdef789",
      "user_id": "64f7b1234567890abcdef123",
      "date": "2025-08-11",
      "time": "18:00:00",
      "location": "Office Building, Mumbai",
      "latitude": "19.0760",
      "longitude": "72.8777",
      "action_type": "punch_out"
    },
    {
      "id": "64f7b1234567890abcdef456",
      "user_id": "64f7b1234567890abcdef123",
      "date": "2025-08-11",
      "time": "09:00:00",
      "location": "Office Building, Mumbai",
      "latitude": "19.0760",
      "longitude": "72.8777",
      "action_type": "punch_in"
    }
  ]
}
```

#### 9. Get Attendance Status
**GET** `/attendance/status/` (**Requires Authorization header**)

Get current attendance status for today.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "date": "2025-08-11",
  "is_punched_in": false,
  "last_action": {
    "id": "64f7b1234567890abcdef789",
    "action_type": "punch_out",
    "time": "18:00:00",
    "location": "Office Building, Mumbai"
  },
  "total_records_today": 2
}
```

#### 10. Logout
**POST** `/logout/` (**Requires Authorization header**)

Logout the employee and invalidate the access token.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "Logout successful"
}
```

### Authentication Notes
- All endpoints except signup, OTP verification, and forgot password require the Authorization header:
  ```
  Authorization: Bearer <access_token>
  ```
- After login, copy the `access` token from the response and use it in the Authorization header for all protected endpoints in Postman.

### Postman Usage
- Import the provided Postman collection JSON file.
- For all protected endpoints, add the Authorization header:
  ```
  Authorization: Bearer <your_access_token>
  ```
- Replace `<your_access_token>` with the token received from the login or OTP verification response.
- You can now test all endpoints directly in Postman.

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "error": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created successfully
- `400`: Bad request (validation errors)
- `401`: Unauthorized (invalid/missing token)
- `404`: Not found
- `500`: Internal server error

## Setup Instructions

### 1. Environment Setup
```bash
# Clone the repository
git clone <repository-url>
cd ems

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your configuration
```

### 2. Database Setup
```bash
# Run Django migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

### 3. MongoDB Setup
Ensure MongoDB is running and update `.env` file:
```
USE_MONGODB=True
MONGODB_CONNECTION_STRING=mongodb://localhost:27017
MONGODB_DATABASE_NAME=EMS
```

### 4. Run Development Server
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/employee/`

## Testing

Run the test suite:
```bash
python test_ems_api.py
```

## Deployment

For production deployment (Render, Railway, etc.):
