# HRMS Django Backend - Project Structure & Setup

## Overview

This is a **production-grade backend framework** for an HR Management System built with Django. The architecture separates business logic (services) from API/database layers, making it highly testable and maintainable.

---

## Project Structure

```
your_django_project/
├── manage.py
├── requirements.txt
│
└── hrms/                          # Main app
    ├── migrations/
    ├── __init__.py
    │
    ├── models.py                  # Django ORM models (YOUR EXISTING DB SCHEMA)
    ├── urls.py                    # API routing
    ├── views.py                   # Request/response handlers (REST endpoints)
    ├── serializers.py             # DRF serializers (if using DRF)
    │
    ├── services/                  # Business logic layer (NEW - THIS IS THE FRAMEWORK)
    │   ├── __init__.py
    │   ├── auth_service.py        # Authentication & authorization
    │   ├── leave_service.py       # Leave management logic
    │   ├── attendance_service.py  # Attendance tracking logic
    │   ├── payroll_service.py     # Payroll calculation logic
    │   ├── profile_service.py     # Employee profile management logic
    │   └── base_service.py        # Shared utilities (optional)
    │
    ├── utils/                     # Helper functions
    │   ├── __init__.py
    │   └── validators.py          # Input validation helpers
    │
    ├── middleware/
    │   ├── __init__.py
    │   └── auth_middleware.py     # JWT/Session authentication
    │
    ├── tests/                     # Unit & integration tests
    │   ├── test_services.py       # Test business logic
    │   ├── test_views.py          # Test API endpoints
    │   └── test_integration.py    # End-to-end tests
    │
    └── admin.py                   # Django admin configuration

hrms_documentation/
├── ARCHITECTURE.md               # Detailed architecture guide
├── django_integration_example.py # Real working examples
└── PROJECT_STRUCTURE.md          # This file
```

---

## Installation & Setup

### 1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install django djangorestframework django-cors-headers pyjwt python-dateutil
```

### 3. Copy Service Files into Your Django Project

From the provided files, copy these into `hrms/services/`:
```bash
# These are the core services (already provided)
- auth_service.py
- leave_service.py
- attendance_service.py
- payroll_service.py
- profile_service.py
```

### 4. Update Django Settings

```python
# settings.py

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'rest_framework',
    'corsheaders',
    'hrms',  # Your HRMS app
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'hrms.middleware.auth_middleware.RoleBasedAccessMiddleware',  # Add custom middleware
]

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}
```

### 5. Update Django URLs

```python
# urls.py (project level)

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('hrms.urls')),  # Include HRMS URLs
]


# hrms/urls.py (app level)

from django.urls import path
from . import views

app_name = 'hrms'

urlpatterns = [
    # Authentication
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    
    # Leave Management
    path('leave/apply/', views.apply_leave, name='apply_leave'),
    path('leave/approve/', views.approve_leave, name='approve_leave'),
    path('leave/list/', views.list_leave_requests, name='list_leaves'),
    
    # Attendance
    path('attendance/check-in/', views.check_in, name='check_in'),
    path('attendance/check-out/', views.check_out, name='check_out'),
    path('attendance/summary/', views.attendance_summary, name='attendance_summary'),
    
    # Payroll
    path('payroll/process/', views.process_monthly_payroll, name='process_payroll'),
    path('payroll/slip/', views.get_salary_slip, name='salary_slip'),
    
    # Profile
    path('employees/<str:employee_id>/profile/', views.get_employee_profile, name='profile'),
    path('employees/<str:employee_id>/profile/update/', views.update_employee_profile, name='update_profile'),
]
```

---

## How the Framework Works

### Request Flow

```
HTTP Request
    ↓
Django View (views.py)
    ↓
Service Layer (services/...)
    ├─ Validation
    ├─ Business Logic
    ├─ Authorization
    └─ Return Result
    ↓
Django ORM (models.py)
    ├─ Save/Update/Fetch
    └─ Database
    ↓
View Serializes Response
    ↓
HTTP Response
```

### Concrete Example: Leave Application

```
1. EMPLOYEE submits: POST /api/leave/apply
   {
       "start_date": "2024-07-15",
       "end_date": "2024-07-20",
       "leave_type": "PAID_LEAVE"
   }

2. DJANGO VIEW receives request
   - Extracts user_id from JWT
   - Validates request format
   
3. SERVICE LAYER executes
   a) LeaveValidationService.validate_dates()
      → Check dates are valid, not in past, etc.
   
   b) LeaveValidationService.check_overlap()
      → Check no approved leaves exist in range
   
   c) LeaveBalanceService.can_apply_leave()
      → Check employee has leave balance
   
   d) Create LeaveRequest object
      → All business rules passed ✓

4. VIEW saves to DATABASE
   - Create DBLeaveRequest record
   - Set status='pending'
   - Save with timestamp

5. VIEW returns response
   {
       "message": "Leave request submitted",
       "request_id": "123456",
       "status": "pending"
   }

6. APPROVER receives notification
   → Views pending requests
   → Calls approve_leave endpoint

7. APPROVAL SERVICE executes
   - LeaveApprovalService.approve_leave()
   - Validates status is 'pending'
   - Updates status to 'approved'
   - Triggers notifications (if implemented)

8. EMPLOYEE sees leave status updated
   → Attendance marked as LEAVE for those dates
   → Cannot override with check-in
```

---

## Key Files & Their Purpose

| File | Purpose | Responsibility |
|------|---------|-----------------|
| `auth_service.py` | User authentication & authorization | Password hashing, role checks, permissions |
| `leave_service.py` | Leave request management | Validation, balance tracking, approvals |
| `attendance_service.py` | Time tracking | Check-in/out, hours calculation, analytics |
| `payroll_service.py` | Salary & compensation | Salary structures, deductions, tax calculation |
| `profile_service.py` | Employee information | Profile CRUD, documents, education records |
| `models.py` | Database schema | Persistence layer (YOUR JOB) |
| `views.py` | API endpoints | Request handling, response formatting |
| `urls.py` | URL routing | Map URLs to views |
| `middleware.py` | Request/response processing | JWT verification, role extraction |

---

## Testing the Framework

### Unit Tests (No Database)

```python
# hrms/tests/test_services.py

from django.test import TestCase
from ..services.leave_service import LeaveValidationService
from datetime import date

class LeaveValidationTestCase(TestCase):
    
    def setUp(self):
        self.validator = LeaveValidationService()
    
    def test_past_date_validation(self):
        """Past dates should be rejected."""
        is_valid, error = self.validator.validate_dates(
            date(2020, 1, 1),
            date(2020, 1, 5)
        )
        self.assertFalse(is_valid)
        self.assertIn('past', error.lower())
    
    def test_valid_future_date(self):
        """Future dates should be accepted."""
        from datetime import timedelta
        today = date.today()
        is_valid, error = self.validator.validate_dates(
            today + timedelta(days=7),
            today + timedelta(days=10)
        )
        self.assertTrue(is_valid)
    
    def test_advance_notice_requirement(self):
        """Immediate leave should require advance notice."""
        from datetime import timedelta
        today = date.today()
        is_valid, error = self.validator.validate_dates(
            today,
            today + timedelta(days=1)
        )
        # Implementation depends on your rules
```

### Integration Tests (With Database)

```python
# hrms/tests/test_integration.py

from django.test import TestCase
from ..models import Employee, LeaveRequest
from ..services.leave_service import LeaveApprovalService, LeaveType, LeaveStatus
from datetime import date

class LeaveWorkflowTestCase(TestCase):
    
    def setUp(self):
        self.employee = Employee.objects.create(
            id='emp_001',
            email='john@company.com',
            first_name='John',
            last_name='Doe'
        )
    
    def test_complete_leave_workflow(self):
        """Test entire leave application and approval flow."""
        
        # 1. Create leave request
        leave = LeaveRequest.objects.create(
            employee=self.employee,
            start_date=date(2024, 7, 15),
            end_date=date(2024, 7, 20),
            leave_type='PAID_LEAVE',
            status='pending',
            remarks='Vacation'
        )
        
        # 2. Approve it
        approval_svc = LeaveApprovalService()
        service_obj = LeaveRequest(
            request_id=str(leave.id),
            employee_id=str(leave.employee_id),
            leave_type=LeaveType.PAID_LEAVE,
            start_date=leave.start_date,
            end_date=leave.end_date,
            status=LeaveStatus.PENDING,
            remarks=leave.remarks,
            created_at=leave.created_at,
        )
        
        approved = approval_svc.approve_leave(service_obj, 'admin_001')
        
        # 3. Verify
        self.assertEqual(approved.status, LeaveStatus.APPROVED)
        self.assertEqual(approved.approver_id, 'admin_001')
```

### Run Tests
```bash
python manage.py test hrms.tests.test_services
python manage.py test hrms.tests.test_integration
```

---

## Common Patterns

### Pattern 1: Validation Before Action
```python
validator = LeaveValidationService()
is_valid, error = validator.validate_dates(start, end)
if not is_valid:
    return error_response(error)

# Proceed if valid
```

### Pattern 2: Service Layer with DB Conversion
```python
# Convert DB → Service
db_obj = LeaveRequest.objects.get(id=request_id)
service_obj = db_obj.to_service_object()

# Process in service
approval_svc = LeaveApprovalService()
result = approval_svc.approve_leave(service_obj, approver_id)

# Convert Service → DB
db_obj.status = result.status.value
db_obj.save()
```

### Pattern 3: Authorization Checks
```python
auth_svc = AuthorizationService()
can_access = auth_svc.can_access_employee_record(
    user_role, user_id, target_emp_id
)
if not can_access:
    raise PermissionError("Unauthorized")
```

### Pattern 4: Role-Based Restrictions
```python
if user_role == UserRole.EMPLOYEE:
    # Only update own fields
    allowed_fields = ['phone', 'address', 'contact_info']
else:
    # Admin can update anything
    allowed_fields = ALL_FIELDS
```

---

## Debugging Tips

### View Service Flow
```python
# In views.py, add logging

import logging
logger = logging.getLogger(__name__)

def apply_leave(request):
    logger.debug(f"Leave application from {user_id}")
    
    # ... validation ...
    logger.debug(f"Validation passed: {validated}")
    
    # ... service call ...
    logger.debug(f"Service returned: {result}")
    
    # ... DB save ...
    logger.debug(f"Saved to DB: {db_record.id}")
```

### Test Service in Isolation
```python
# Don't need Django to test services
from hrms.services.leave_service import LeaveValidationService

validator = LeaveValidationService()
is_valid, error = validator.validate_dates(date(2024, 7, 15), date(2024, 7, 20))
print(f"Valid: {is_valid}, Error: {error}")
```

### Check Authorization
```python
from hrms.services.auth_service import AuthorizationService, UserRole

auth = AuthorizationService()
perms = AuthorizationService.ROLE_PERMISSIONS[UserRole.EMPLOYEE]
print(f"Employee permissions: {perms}")
```

---

## Performance Optimization

### 1. Use select_related() and prefetch_related()
```python
# Bad: N+1 queries
employees = Employee.objects.all()
for emp in employees:
    print(emp.department.name)  # Extra query per employee

# Good: Single query with join
employees = Employee.objects.select_related('department')
```

### 2. Batch Operations
```python
# Bad: Multiple inserts
for emp_id, bonus in bonuses.items():
    payroll = PayrollRecord.objects.create(...)

# Good: Bulk insert
records = [PayrollRecord(...) for emp_id, bonus in bonuses.items()]
PayrollRecord.objects.bulk_create(records, batch_size=100)
```

### 3. Cache Service Results
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_leave_strategies():
    return LeaveBalanceService.LEAVE_STRATEGIES
```

---

## Extending the Framework

To add a new feature (e.g., Performance Reviews):

1. **Create service module** → `performance_service.py`
2. **Define dataclasses** → PerformanceReview, ReviewCriteria
3. **Implement business logic** → PerformanceService
4. **Add authorization** → Update auth_service.py roles
5. **Create Django models** → Update models.py
6. **Create views** → Update views.py
7. **Add tests** → Update tests/

The framework scales horizontally—each new feature is an independent service module.

---

## Support & Debugging

### Common Issues

**Issue**: Service returns but DB doesn't update
**Solution**: Wrap DB operations in `transaction.atomic()`

**Issue**: Permission denied on valid user
**Solution**: Check JWT token has correct role. Debug with: `print(request.user.role)`

**Issue**: Overlap detection not working
**Solution**: Ensure existing_leaves are all in same format. Convert all to service objects.

**Issue**: Payroll calculation seems wrong
**Solution**: Verify salary structure has correct allowances/deductions. Check attendance data.

---

## Next Steps

1. **Populate models.py** with Django ORM models matching your DB schema
2. **Implement views.py** using the provided examples as templates
3. **Configure urls.py** with your API endpoints
4. **Write tests** to validate business logic
5. **Deploy** with your Django app

---

## Summary

You now have a **production-ready backend framework** with:
- ✅ Comprehensive business logic (leave, attendance, payroll, profiles)
- ✅ Role-based access control
- ✅ Testable service-oriented architecture
- ✅ Clear separation between API, services, and database layers
- ✅ Extensible patterns for adding new features

This is how **quant/big tech companies** structure their backend systems—clean, scalable, and maintainable.

**Good luck building. Code like you're going to maintain it for 5 years.**
