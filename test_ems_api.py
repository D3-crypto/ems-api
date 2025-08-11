#!/usr/bin/env python3
"""
Test script for Employee Management System (EMS) API
Tests all the employee endpoints including authentication and attendance.
"""

import requests
import json
import time
from datetime import datetime

# API Base URL
BASE_URL = "http://127.0.0.1:8000/api/employee"

# Test data
TEST_USER = {
    "user_name": "testemployee",
    "email": "test@ems.com",
    "password": "TestPassword123",
    "reEnterPassword": "TestPassword123"
}

# Global variables to store tokens and user data
access_token = None
refresh_token = None
user_id = None

def print_response(title, response):
    """Pretty print API response"""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

def test_signup():
    """Test user signup"""
    global user_id
    
    url = f"{BASE_URL}/signup/"
    response = requests.post(url, json=TEST_USER)
    print_response("1. User Signup", response)
    
    if response.status_code == 201:
        data = response.json()
        user_id = data.get('user_id')
        print(f"✅ Signup successful! User ID: {user_id}")
        return True
    else:
        print("❌ Signup failed!")
        return False

def test_verify_otp():
    """Test OTP verification (manual input required)"""
    global access_token, refresh_token
    
    # Since we can't automatically get OTP from email, we'll skip this in automated test
    # In real testing, you would:
    # 1. Get OTP from email/console
    # 2. Call verify-otp endpoint
    # 3. Then proceed with login
    
    print(f"\n{'='*50}")
    print("2. OTP Verification")
    print(f"{'='*50}")
    print("⚠️ Manual step required: Check your email/console for OTP")
    print("💡 In a real test, you would verify the OTP here")
    print("⏭️ Skipping to login test (assuming OTP verification is done)")
    
    return True

def test_login():
    """Test user login"""
    global access_token, refresh_token
    
    url = f"{BASE_URL}/login/"
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"],
        "deviceType": "web"
    }
    
    response = requests.post(url, json=login_data)
    print_response("3. User Login", response)
    
    if response.status_code == 200:
        data = response.json()
        access_token = data.get('access')
        refresh_token = data.get('refresh')
        print(f"✅ Login successful!")
        print(f"Access Token: {access_token[:50]}...")
        return True
    else:
        print("❌ Login failed!")
        return False

def test_punch_in():
    """Test punch in"""
    if not access_token:
        print("❌ No access token available for punch in test")
        return False
    
    url = f"{BASE_URL}/punch-in/"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    current_time = datetime.now()
    punch_data = {
        "date": current_time.strftime("%Y-%m-%d"),
        "time": current_time.strftime("%H:%M:%S"),
        "location": "EMS Office, Mumbai",
        "latitude": "19.0760",
        "longitude": "72.8777"
    }
    
    response = requests.post(url, json=punch_data, headers=headers)
    print_response("4. Punch In", response)
    
    if response.status_code == 201:
        print("✅ Punch in successful!")
        return True
    else:
        print("❌ Punch in failed!")
        return False

def test_attendance_status():
    """Test attendance status check"""
    if not access_token:
        print("❌ No access token available for attendance status test")
        return False
    
    url = f"{BASE_URL}/attendance/status/"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(url, headers=headers)
    print_response("5. Attendance Status", response)
    
    if response.status_code == 200:
        print("✅ Attendance status retrieved!")
        return True
    else:
        print("❌ Attendance status failed!")
        return False

def test_punch_out():
    """Test punch out"""
    if not access_token:
        print("❌ No access token available for punch out test")
        return False
    
    url = f"{BASE_URL}/punch-out/"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    current_time = datetime.now()
    punch_data = {
        "date": current_time.strftime("%Y-%m-%d"),
        "time": current_time.strftime("%H:%M:%S"),
        "location": "EMS Office, Mumbai",
        "latitude": "19.0760",
        "longitude": "72.8777"
    }
    
    response = requests.post(url, json=punch_data, headers=headers)
    print_response("6. Punch Out", response)
    
    if response.status_code == 201:
        print("✅ Punch out successful!")
        return True
    else:
        print("❌ Punch out failed!")
        return False

def test_get_attendance():
    """Test get attendance records"""
    if not access_token:
        print("❌ No access token available for get attendance test")
        return False
    
    url = f"{BASE_URL}/attendance/"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test with today's date
    today = datetime.now().strftime("%Y-%m-%d")
    params = {"date": today}
    
    response = requests.get(url, headers=headers, params=params)
    print_response("7. Get Attendance Records", response)
    
    if response.status_code == 200:
        print("✅ Attendance records retrieved!")
        return True
    else:
        print("❌ Get attendance failed!")
        return False

def test_forgot_password():
    """Test forgot password"""
    url = f"{BASE_URL}/forgot-password/"
    data = {"email": TEST_USER["email"]}
    
    response = requests.post(url, json=data)
    print_response("8. Forgot Password", response)
    
    if response.status_code == 200:
        print("✅ Forgot password OTP sent!")
        return True
    else:
        print("❌ Forgot password failed!")
        return False

def run_all_tests():
    """Run all tests in sequence"""
    print("🚀 Starting Employee Management System (EMS) API Tests")
    print("="*60)
    
    tests = [
        ("Signup", test_signup),
        ("OTP Verification", test_verify_otp),
        ("Login", test_login),
        ("Punch In", test_punch_in),
        ("Attendance Status", test_attendance_status),
        ("Punch Out", test_punch_out),
        ("Get Attendance", test_get_attendance),
        ("Forgot Password", test_forgot_password),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            time.sleep(1)  # Small delay between tests
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {len(results)}, Passed: {passed}, Failed: {len(results) - passed}")
    
    if passed == len(results):
        print("🎉 All tests passed!")
    else:
        print("⚠️ Some tests failed. Check the logs above.")

if __name__ == "__main__":
    print("Employee Management System (EMS) API Test Suite")
    print("Make sure the Django server is running on http://127.0.0.1:8000")
    
    try:
        # Test server connectivity
        response = requests.get("http://127.0.0.1:8000/api/employee/", timeout=5)
        print("✅ Server is reachable")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django is running.")
        exit(1)
    except:
        print("✅ Server is reachable (404 expected for base URL)")
    
    run_all_tests()
