# HRMS Backend Architecture Guide

This is a **service-oriented backend framework** for the Human Resource Management System. It provides business logic, validation, and authorization layers—completely decoupled from your API and database implementations.

## Philosophy

This architecture emphasizes:
- **Separation of Concerns**: Services handle business logic; Django ORM/API handle I/O
- **Testability**: Pure functions and dataclasses make unit testing straightforward
- **Scalability**: Service layer can be cached, distributed, or migrated independently
- **Type Safety**: Dataclasses and Enums prevent invalid state transitions
- **Readability**: Each service has one responsibility; methods are small and explicit

---

## Core Modules

### 1. **auth_service.py** - Authentication & Authorization

**Responsibility**: User authentication, password management, role-based access control (RBAC).

**Key Classes**:
- `AuthenticationService`: Password hashing/verification, email validation
- `AuthorizationService`: Role-based permissions, permission checks
- `UserRole` enum: ADMIN, HR_OFFICER, EMPLOYEE

**Decorators**:
```python
@require_role(UserRole.ADMIN)
def delete_employee(employee_id: str): ...

@require_permission('approve_leave')
def approve_leave_request(request_id: str): ...
```

**Integration with Django**:
- Wrap decorators around Django views
- Use `AuthenticationService` in user registration/login endpoints
- Store user role from `AuthorizationService` in JWT payload or session

---

### 2. **leave_service.py** - Leave Management

**Responsibility**: Leave requests, approvals, balance tracking, policy enforcement.

**Key Classes**:
- `LeaveBalanceService`: Calculate remaining balance using strategy pattern
- `LeaveValidationService`: Business rules (advance notice, overlap checking, max duration)
- `LeaveApprovalService`: Approval/rejection workflow
- `LeaveReportService`: Generate leave summaries and analytics

**Workflow Example**:
```python
# 1. Validate request
validation = LeaveValidationService()
can_apply, reason = validation.validate_dates(start, end)
can_apply2, reason2 = validation.check_overlap(emp_id, start, end, existing_leaves)

# 2. Check balance
balance_svc = LeaveBalanceService()
can_apply3, reason3 = balance_svc.can_apply_leave(emp_id, leave_type, days, used_days)

# 3. Create and approve
leave = LeaveRequest(...)
approval_svc = LeaveApprovalService()
approved = approval_svc.approve_leave(leave, approver_id, comments)
```

**Strategy Pattern** (Extensible):
Different leave types have different policies (PaidLeaveStrategy, SickLeaveStrategy, etc.).
Add new leave types by creating a new strategy class.

---

### 3. **attendance_service.py** - Attendance Tracking

**Responsibility**: Check-in/check-out, attendance validation, analytics, and reporting.

**Key Classes**:
- `AttendanceTrackingService`: Record check-in/out
- `AttendanceValidationService`: Business rules (working hours, late check-in, etc.)
- `AttendanceAnalyticsService`: Percentage, summaries, chronic absentee identification
- `AttendanceReportService`: Format data for employee/admin views

**Workflow Example**:
```python
tracking_svc = AttendanceTrackingService()

# Employee checks in
record = tracking_svc.check_in(emp_id, time(9, 30))

# Employee checks out
record = tracking_svc.check_out(record, time(17, 45))

# Get summary
analytics = AttendanceAnalyticsService()
summary = analytics.get_attendance_summary(emp_id, all_records, year=2024, month=7)
percentage = analytics.get_attendance_percentage(emp_id, all_records)
```

**Analytics Capability**:
- Daily/weekly/monthly views
- Attendance percentage calculation
- Chronic absentee detection
- Hours worked calculation

---

### 4. **payroll_service.py** - Payroll & Salary Management

**Responsibility**: Salary structure, payroll calculation, deductions, finalization.

**Key Classes**:
- `SalaryStructure`: Define fixed components (base, allowances, deductions)
- `PayrollRecord`: Monthly payroll with adjustments (bonus, attendance impact)
- `PayrollCalculationService`: Income tax, PF, deductions (pluggable tax rules)
- `PayrollFinalizationService`: Lock payroll after processing
- `PayrollReportService`: Salary slips and summaries

**Workflow Example**:
```python
# Define salary structure
salary_svc = SalaryStructureService()
structure = salary_svc.create_salary_structure(
    emp_id,
    base_salary=50000,
    allowances={'HRA': 15000, 'DA': 5000},
    admin_id=admin_id
)

# Generate payroll for a month
calc_svc = PayrollCalculationService()
payroll_breakdown = calc_svc.generate_payroll(
    structure,
    working_days=22,
    days_worked=20,
    bonus=5000
)

# Finalize
finalize_svc = PayrollFinalizationService()
payroll = finalize_svc.finalize_payroll(payroll_record, admin_id)

# Get salary slip
report_svc = PayrollReportService()
slip = report_svc.get_salary_slip(payroll)
```

**Pluggable Tax Rules**:
Methods like `calculate_income_tax()` can be replaced per jurisdiction.

---

### 5. **profile_service.py** - Employee Profile Management

**Responsibility**: Profile CRUD, education records, documents, employee directory.

**Key Classes**:
- `EmployeeProfile`: Complete profile with personal, job, contact info
- `ProfileManagementService`: Create/update with role-based restrictions
- `EducationService`: Manage qualifications
- `DocumentService`: Manage certificates and IDs with expiry tracking
- `EmployeeDirectoryService`: Search, filter, reporting structure

**Workflow Example**:
```python
# Create profile
mgmt_svc = ProfileManagementService()
profile = mgmt_svc.create_profile(profile_obj, admin_id)

# Employee updates own info (restricted fields)
updates = {'address': 'New Address', 'phone': '9999999999'}
profile = mgmt_svc.update_profile(profile, updates, emp_id, 'employee')

# Add document
doc_svc = DocumentService()
doc = doc_svc.add_document(profile, 'PAN', 'ABCDE1234F', expiry_date=date(2030, 12, 31))

# Check expiry
is_valid, msg = doc_svc.verify_document_expiry(doc)

# Search employees
dir_svc = EmployeeDirectoryService()
results = dir_svc.search_employees(all_profiles, "john")
dept_employees = dir_svc.get_department_employees(all_profiles, Department.ENGINEERING)
```

**Role-Based Field Restrictions**:
- Employees: Can update address, phone, contact info
- Admins: Can update all fields including job details, salary info

---

## Integration with Django

### Views Layer
```python
# hrms/views.py
from django.views.decorators.http import require_http_methods
from .auth_service import require_permission, UserRole
from .leave_service import LeaveValidationService, LeaveBalanceService

@require_permission('apply_for_leave')
@require_http_methods(['POST'])
def apply_leave(request):
    # Extract user role from JWT/session
    user_role = request.user.role
    
    # Deserialize request → service call
    start_date = parse_date(request.data['start_date'])
    end_date = parse_date(request.data['end_date'])
    leave_type = LeaveType[request.data['type']]
    
    # Validate
    validator = LeaveValidationService()
    is_valid, error = validator.validate_dates(start_date, end_date)
    if not is_valid:
        return JsonResponse({'error': error}, status=400)
    
    # Check balance
    balance_svc = LeaveBalanceService()
    can_apply, error = balance_svc.can_apply_leave(
        request.user.id, leave_type, days, used_days
    )
    if not can_apply:
        return JsonResponse({'error': error}, status=400)
    
    # Create in DB and return
    leave_request = LeaveRequest.objects.create(...)  # Your ORM
    return JsonResponse(serialize_leave(leave_request))
```

### Models Layer
```python
# hrms/models.py - Already implemented by you
# Our services work WITH your ORM:

from .leave_service import LeaveRequest as ServiceLeaveRequest
from .leave_service import LeaveStatus

class LeaveRequest(models.Model):
    employee = ForeignKey(Employee, on_delete=models.CASCADE)
    start_date = DateField()
    end_date = DateField()
    status = CharField(max_length=20, choices=[(s.value, s.value) for s in LeaveStatus])
    
    def to_service_object(self) -> ServiceLeaveRequest:
        """Convert DB model to service dataclass."""
        return ServiceLeaveRequest(
            request_id=str(self.id),
            employee_id=str(self.employee_id),
            leave_type=LeaveType[self.leave_type.upper()],
            start_date=self.start_date,
            end_date=self.end_date,
            status=LeaveStatus[self.status.upper()],
            remarks=self.remarks,
            created_at=self.created_at,
        )
    
    @staticmethod
    def from_service_object(service_obj: ServiceLeaveRequest):
        """Convert service dataclass back to DB model."""
        return LeaveRequest.objects.update_or_create(
            id=service_obj.request_id,
            defaults={
                'status': service_obj.status.value,
                'approved_at': service_obj.approved_at,
            }
        )
```

### Middleware / Permission Checking
```python
# hrms/middleware.py
from .auth_service import AuthorizationService

class RoleBasedAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Extract role from JWT
        token = request.META.get('HTTP_AUTHORIZATION')
        user_role = extract_role_from_jwt(token)
        request.user_role = user_role
        
        response = self.get_response(request)
        return response
```

---

## Design Patterns Used

### 1. **Strategy Pattern** (LeaveBalanceService)
Different leave types have different policies. Strategies are swappable:
```python
strategy = LeaveBalanceService.get_strategy(LeaveType.PAID_LEAVE)
allocation = strategy.get_annual_allocation()
```

### 2. **Decorator Pattern** (Permissions)
Wrap functions with authorization checks:
```python
@require_permission('approve_leave')
def approve_leave(request_id):
    ...
```

### 3. **Service Locator** (Future Improvement)
For caching/complex dependencies, use a service registry:
```python
services = ServiceContainer()
services.register('leave_service', LeaveApprovalService())
leave_svc = services.get('leave_service')
```

### 4. **Builder Pattern** (PayrollRecord)
Complex objects are built step by step:
```python
payroll = PayrollRecord(employee_id, salary_month, structure)
payroll.bonus = 5000
payroll.days_worked = 20
payroll = finalize_svc.finalize_payroll(payroll, admin_id)
```

---

## Testing Strategy

### Unit Tests (No DB)
```python
# tests/test_leave_service.py
from leave_service import LeaveValidationService, LeaveStatus

def test_leave_validation_past_date():
    validator = LeaveValidationService()
    is_valid, error = validator.validate_dates(
        date(2020, 1, 1),
        date(2020, 1, 5)
    )
    assert not is_valid
    assert "past" in error.lower()

def test_overlap_detection():
    existing = [LeaveRequest(..., start=date(2024, 7, 10), end=date(2024, 7, 15))]
    is_valid, _ = validator.check_overlap(
        'emp_1',
        date(2024, 7, 12),
        date(2024, 7, 18),
        existing
    )
    assert not is_valid
```

### Integration Tests (With Django ORM)
```python
@pytest.mark.django_db
def test_leave_approval_workflow():
    emp = Employee.objects.create(id='emp_1')
    leave = LeaveRequest.objects.create(employee=emp, status='pending')
    
    approval_svc = LeaveApprovalService()
    service_obj = leave.to_service_object()
    approved = approval_svc.approve_leave(service_obj, 'admin_1')
    
    assert approved.status == LeaveStatus.APPROVED
```

---

## Performance Considerations

### Caching Strategy
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_leave_strategies():
    return LeaveBalanceService.LEAVE_STRATEGIES
```

### Bulk Operations
```python
# Process payroll for 100 employees
payrolls = [
    PayrollCalculationService.generate_payroll(struct, wd, dw)
    for struct, wd, dw in employee_data
]
# Insert all at once with bulk_create()
PayrollRecord.objects.bulk_create([...])
```

### Query Optimization (In Django Views)
```python
# Don't N+1 query
employees = Employee.objects.select_related('department').prefetch_related('leave_requests')

# Convert to service objects
profiles = [ProfileManagementService.convert(emp) for emp in employees]

# Use service layer
dir_svc = EmployeeDirectoryService()
dept_results = dir_svc.get_department_employees(profiles, Department.ENGINEERING)
```

---

## Extending the Framework

### Adding a New Feature (e.g., Performance Reviews)

1. **Create a new service module** (`performance_service.py`)
   ```python
   class PerformanceReview:
       reviewer_id: str
       rating: float  # 1-5
       feedback: str
   
   class PerformanceService:
       def submit_review(self, review: PerformanceReview) -> bool: ...
       def get_employee_reviews(self, emp_id: str) -> List[PerformanceReview]: ...
   ```

2. **Add authorization** in `auth_service.py`
   ```python
   'submit_review': UserRole.MANAGER
   'view_reviews': UserRole.ADMIN
   ```

3. **Create Django model** and views
4. **Integrate** service layer in views

---

## Key Takeaways

- **Services are stateless**: All state is passed as parameters
- **Enums prevent invalid states**: Use `LeaveStatus.APPROVED` instead of string "approved"
- **Validation before operations**: All methods validate input
- **Clear separation**: DB layer (models), API layer (views), Business logic (services)
- **Testable**: All services have no dependencies on Django ORM
- **Extensible**: Use pattern overrides (strategy, decorators) to customize behavior

This is a framework designed for **production systems** where correctness, testability, and maintainability matter.
