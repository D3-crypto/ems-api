"""
Django management script to clean up expired OTPs (older than 10 minutes) from MongoDB.
Usage:
    python cleanup_expired_otps.py
"""

from mongo_models import MongoOTP

def main():
    deleted_count = MongoOTP.cleanup_expired_otps()
    print(f"Deleted {deleted_count} expired OTP(s) from MongoDB.")

if __name__ == "__main__":
    main()
