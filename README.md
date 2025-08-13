# Employee Management System (EMS) API

A Django REST API for employee management, attendance tracking, and authentication, using MongoDB for data storage.

## Features
- JWT-based authentication (SimpleJWT)
- OTP-based password reset
- Single device login enforcement
- Punch-in/punch-out attendance tracking
- Session management and logout
- MongoDB backend for user, session, and attendance data

## Setup Instructions
1. **Clone the repository:**
   ```sh
   git clone https://github.com/D3-crypto/ems-api.git
   cd ems-api
   ```
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
3. **Configure environment:**
   - Copy `.env.example` to `.env` and update MongoDB and Django settings as needed.
4. **Run migrations:**
   ```sh
   python manage.py migrate
   ```
5. **Start the server:**
   ```sh
   python manage.py runserver
   ```

## API Endpoints
- **Authentication:**
  - `POST /api/employee/signup/` — User signup with email and password
  - `POST /api/employee/verify-otp/` — Verify user email with OTP
  - `POST /api/login/` — Login with email and password
  - `POST /api/logout/` — Logout and deactivate session
  - `POST /api/forgot-password/` — Request OTP for password reset
  - `POST /api/reset-password/` — Reset password using OTP
- **Attendance:**
  - `POST /api/punch-in/` — Punch in (requires JWT)
  - `POST /api/punch-out/` — Punch out (requires JWT)
  - `GET /api/attendance/` — Get all attendance records (requires JWT, Admin only)
- **Leave:**
  - `POST /api/employee/leave/` — Apply for leave (requires JWT)
  - `GET /api/employee/leave/` — List leave applications (employees list their own, admins list all) (requires JWT)
  - `PATCH /api/employee/leave/admin/<leave_id>/` — Approve or reject a leave application (requires JWT, Admin only)

## Usage Notes
- All protected endpoints require the `Authorization: Bearer <access_token>` header.
- Attendance records are stored in a dedicated MongoDB collection.
- Only one active session per user is allowed.

## Documentation & Testing
- See `EMS_API_DOCUMENTATION.md` for detailed API docs.
- Use the provided Postman collection (`EMS_API_Postman_Collection.json`) for testing.

## Admin Functionality
The system supports an \'admin\' role with elevated privileges. Currently, only administrators can view all attendance records and approve/reject leave applications.

To create an admin user, you can use the `make_admin` management command:

