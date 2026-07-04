"""
PRACTICAL EXAMPLE: Integrating Services with Django Views

This shows how to wire up the service layer with actual Django views,
handling request/response cycles and DB transactions.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from datetime import datetime, date
from typing import Optional

# Import service classes
from .auth_service import (
    AuthenticationService, AuthorizationService,
    require_permission, require_role, UserRole
)
from .leave_service import (
    LeaveValidationService, LeaveBalanceService,
    LeaveApprovalService, LeaveRequest as ServiceLeaveRequest,
    LeaveType, LeaveStatus
)
from .attendance_service import (
    AttendanceTrackingService, AttendanceValidationService,
    AttendanceRecord, AttendanceStatus
)
from .payroll_service import (
    SalaryStructureService, PayrollCalculationService,
    PayrollFinalizationService, PayrollReportService
)
from .profile_service import (
    ProfileManagementService, EmployeeDirectoryService,
    DocumentService
)

# Your Django models (already exist)
from .models import (
    Employee, LeaveRequest as DBLeaveRequest, 
    AttendanceRecord as DBAttendanceRecord,
    PayrollRecord as DBPayrollRecord,
)


# ============================================================================
# HELPER FUNCTIONS: Bridge between HTTP and Services
# ============================================================================

def extract_user_info(request):
    """Extract user info from JWT token or session."""
    # In production: decode JWT from Authorization header
    user_id = request.user.id  # or parse JWT
    user_role = UserRole(request.user.role)
    return user_id, user_role


def parse_date(date_str: str) -> date:
    """Parse ISO date string."""
    return datetime.fromisoformat(date_str).date()


def serialize_leave_request(db_obj: DBLeaveRequest) -> dict:
    """Convert DB model to JSON-serializable dict."""
    return {
        'request_id': str(db_obj.id),
        'employee_id': str(db_obj.employee_id),
        'start_date': db_obj.start_date.isoformat(),
        'end_date': db_obj.end_date.isoformat(),
        'leave_type': db_obj.leave_type,
        'status': db_obj.status,
        'remarks': db_obj.remarks,
        'created_at': db_obj.created_at.isoformat(),
    }


def service_to_db_leave(service_obj: ServiceLeaveRequest) -> DBLeaveRequest:
    """Convert service object back to DB model."""
    return DBLeaveRequest(
        id=service_obj.request_id,
        status=service_obj.status.value,
        approver_id=service_obj.approver_id,
        approval_comments=service_obj.approval_comments,
        approved_at=service_obj.approved_at,
    )


# ============================================================================
# VIEWS: Leave Management
# ============================================================================

@require_http_methods(['POST'])
def apply_leave(request):
    """
    POST /api/leave/apply
    
    Request body:
    {
        "start_date": "2024-07-15",
        "end_date": "2024-07-20",
        "leave_type": "PAID_LEAVE",
        "remarks": "Vacation"
    }
    """
    try:
        user_id, user_role = extract_user_info(request)
        
        # Parse request
        data = request.JSON
        start_date = parse_date(data['start_date'])
        end_date = parse_date(data['end_date'])
        leave_type = LeaveType[data['leave_type']]
        remarks = data.get('remarks', '')
        
        # Get employee record for balance calculation
        employee = Employee.objects.get(id=user_id)
        
        # ===== SERVICE LAYER EXECUTION =====
        
        # 1. Validate dates
        validator = LeaveValidationService()
        is_valid, error = validator.validate_dates(start_date, end_date)
        if not is_valid:
            return JsonResponse({'error': error}, status=400)
        
        # 2. Check for overlaps with existing approvals
        existing_leaves = DBLeaveRequest.objects.filter(
            employee_id=user_id,
            status='approved'
        )
        existing_service_objects = [
            ServiceLeaveRequest(
                request_id=str(l.id),
                employee_id=str(l.employee_id),
                leave_type=LeaveType[l.leave_type],
                start_date=l.start_date,
                end_date=l.end_date,
                status=LeaveStatus[l.status.upper()],
                remarks=l.remarks,
                created_at=l.created_at,
            )
            for l in existing_leaves
        ]
        
        is_valid, error = validator.check_overlap(
            user_id, start_date, end_date, existing_service_objects
        )
        if not is_valid:
            return JsonResponse({'error': error}, status=400)
        
        # 3. Check leave balance
        balance_svc = LeaveBalanceService()
        
        # Calculate days already used this year
        used_days = DBLeaveRequest.objects.filter(
            employee_id=user_id,
            leave_type=leave_type.value,
            status='approved',
            start_date__year=datetime.now().year,
        ).count()
        
        requested_days = (end_date - start_date).days + 1
        can_apply, error = balance_svc.can_apply_leave(
            user_id, leave_type, requested_days, used_days
        )
        if not can_apply:
            return JsonResponse({'error': error}, status=400)
        
        # 4. Create leave request in DB
        with transaction.atomic():
            leave_record = DBLeaveRequest.objects.create(
                employee=employee,
                start_date=start_date,
                end_date=end_date,
                leave_type=leave_type.value,
                status='pending',
                remarks=remarks,
                created_at=datetime.now(),
            )
        
        return JsonResponse({
            'message': 'Leave request submitted',
            'request_id': str(leave_record.id),
            'status': 'pending',
        }, status=201)
        
    except KeyError as e:
        return JsonResponse({'error': f'Missing field: {e}'}, status=400)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
@require_permission('approve_leave')
def approve_leave(request):
    """
    POST /api/leave/{request_id}/approve
    
    Request body:
    {
        "comments": "Approved"
    }
    """
    try:
        user_id, user_role = extract_user_info(request)
        leave_request_id = request.GET.get('request_id')
        
        # Get leave request
        leave_db = DBLeaveRequest.objects.get(id=leave_request_id)
        
        if leave_db.status != 'pending':
            return JsonResponse(
                {'error': f'Cannot approve leave with status: {leave_db.status}'},
                status=400
            )
        
        # ===== SERVICE LAYER EXECUTION =====
        approval_svc = LeaveApprovalService()
        
        # Convert to service object
        leave_service = ServiceLeaveRequest(
            request_id=str(leave_db.id),
            employee_id=str(leave_db.employee_id),
            leave_type=LeaveType[leave_db.leave_type],
            start_date=leave_db.start_date,
            end_date=leave_db.end_date,
            status=LeaveStatus[leave_db.status.upper()],
            remarks=leave_db.remarks,
            created_at=leave_db.created_at,
        )
        
        # Approve in service layer
        comments = request.JSON.get('comments')
        approved = approval_svc.approve_leave(leave_service, user_id, comments)
        
        # ===== UPDATE DATABASE =====
        with transaction.atomic():
            leave_db.status = approved.status.value
            leave_db.approver_id = user_id
            leave_db.approval_comments = comments
            leave_db.approved_at = approved.approved_at
            leave_db.save()
        
        return JsonResponse({
            'message': 'Leave approved',
            'request_id': str(leave_db.id),
            'status': leave_db.status,
        })
        
    except DBLeaveRequest.DoesNotExist:
        return JsonResponse({'error': 'Leave request not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# VIEWS: Attendance Management
# ============================================================================

@require_http_methods(['POST'])
def check_in(request):
    """
    POST /api/attendance/check-in
    
    Request body:
    {
        "check_in_time": "09:30:00"
    }
    """
    try:
        user_id, _ = extract_user_info(request)
        employee = Employee.objects.get(id=user_id)
        
        # Parse time
        time_str = request.JSON['check_in_time']
        check_in_time = datetime.fromisoformat(time_str).time()
        
        # ===== SERVICE LAYER EXECUTION =====
        tracking_svc = AttendanceTrackingService()
        
        # Check-in
        attendance_record = tracking_svc.check_in(user_id, check_in_time)
        
        # ===== SAVE TO DATABASE =====
        with transaction.atomic():
            db_record = DBAttendanceRecord.objects.create(
                employee=employee,
                date=date.today(),
                status=attendance_record.status.value,
                check_in_time=attendance_record.check_in_time,
                marked_at=attendance_record.marked_at,
            )
        
        return JsonResponse({
            'message': 'Checked in',
            'time': db_record.check_in_time.isoformat(),
            'date': db_record.date.isoformat(),
        })
        
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
def check_out(request):
    """
    POST /api/attendance/check-out
    
    Request body:
    {
        "check_out_time": "18:45:00"
    }
    """
    try:
        user_id, _ = extract_user_info(request)
        
        # Get today's attendance record
        db_record = DBAttendanceRecord.objects.get(
            employee_id=user_id,
            date=date.today()
        )
        
        # Parse time
        time_str = request.JSON['check_out_time']
        check_out_time = datetime.fromisoformat(time_str).time()
        
        # ===== SERVICE LAYER EXECUTION =====
        tracking_svc = AttendanceTrackingService()
        
        # Convert DB record to service object
        attendance_service = AttendanceRecord(
            employee_id=str(db_record.employee_id),
            date=db_record.date,
            status=AttendanceStatus[db_record.status.upper()],
            check_in_time=db_record.check_in_time,
            check_out_time=db_record.check_out_time,
        )
        
        # Check out
        updated = tracking_svc.check_out(attendance_service, check_out_time)
        
        # ===== UPDATE DATABASE =====
        db_record.check_out_time = updated.check_out_time
        db_record.status = updated.status.value
        db_record.save()
        
        hours = updated.get_hours_worked()
        
        return JsonResponse({
            'message': 'Checked out',
            'time': db_record.check_out_time.isoformat(),
            'hours_worked': round(hours, 2) if hours else None,
            'status': db_record.status,
        })
        
    except DBAttendanceRecord.DoesNotExist:
        return JsonResponse(
            {'error': 'No check-in record found for today'},
            status=404
        )
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# VIEWS: Payroll Management
# ============================================================================

@require_http_methods(['POST'])
@require_permission('update_payroll')
def process_monthly_payroll(request):
    """
    POST /api/payroll/process
    
    Request body:
    {
        "month": "2024-07",
        "working_days": 22,
        "bonuses": {"emp_1": 5000, "emp_2": 3000}
    }
    """
    try:
        user_id, _ = extract_user_info(request)
        
        data = request.JSON
        month_str = data['month']  # "2024-07"
        salary_month = datetime.fromisoformat(f"{month_str}-01").date()
        working_days = data['working_days']
        bonuses = data.get('bonuses', {})
        
        # Get all employees
        employees = Employee.objects.all()
        
        # Get attendance for the month
        attendance_records = DBAttendanceRecord.objects.filter(
            date__year=salary_month.year,
            date__month=salary_month.month,
        )
        
        payrolls_to_create = []
        
        for employee in employees:
            # ===== SERVICE LAYER EXECUTION =====
            
            # Get salary structure
            salary_structure = employee.salary_structure
            
            # Calculate days worked
            emp_attendance = attendance_records.filter(employee=employee)
            days_worked = emp_attendance.filter(status='present').count()
            
            # Calculate payroll
            calc_svc = PayrollCalculationService()
            bonus = bonuses.get(str(employee.id), 0)
            
            payroll_breakdown = calc_svc.generate_payroll(
                salary_structure,
                working_days=working_days,
                days_worked=days_worked,
                bonus=bonus,
            )
            
            # Create payroll record
            payroll = DBPayrollRecord(
                employee=employee,
                salary_month=salary_month,
                working_days_in_month=working_days,
                days_worked=days_worked,
                bonus=bonus,
                gross_salary=payroll_breakdown['adjusted_gross'],
                net_salary=payroll_breakdown['net_salary'],
                created_by=user_id,
                created_at=datetime.now(),
            )
            payrolls_to_create.append(payroll)
        
        # ===== BULK CREATE IN DATABASE =====
        with transaction.atomic():
            DBPayrollRecord.objects.bulk_create(
                payrolls_to_create,
                batch_size=100,
            )
        
        return JsonResponse({
            'message': f'Payroll processed for {len(payrolls_to_create)} employees',
            'month': month_str,
            'count': len(payrolls_to_create),
        }, status=201)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['GET'])
def get_salary_slip(request):
    """
    GET /api/payroll/{payroll_id}/slip
    """
    try:
        user_id, user_role = extract_user_info(request)
        payroll_id = request.GET.get('payroll_id')
        
        payroll_db = DBPayrollRecord.objects.get(id=payroll_id)
        
        # Employee can only view own slip
        if user_role == UserRole.EMPLOYEE and str(payroll_db.employee_id) != user_id:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # ===== SERVICE LAYER EXECUTION =====
        report_svc = PayrollReportService()
        
        # For this, we need the full payroll record in service format
        # (In production, extend PayrollReportService to accept DB objects)
        slip = {
            'employee_id': str(payroll_db.employee_id),
            'month': payroll_db.salary_month.strftime('%B %Y'),
            'gross_salary': float(payroll_db.gross_salary),
            'net_salary': float(payroll_db.net_salary),
            'working_days': payroll_db.working_days_in_month,
            'days_worked': payroll_db.days_worked,
        }
        
        return JsonResponse(slip)
        
    except DBPayrollRecord.DoesNotExist:
        return JsonResponse({'error': 'Payroll not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# VIEWS: Employee Profile
# ============================================================================

@require_http_methods(['GET'])
def get_employee_profile(request):
    """
    GET /api/employees/{employee_id}/profile
    """
    try:
        user_id, user_role = extract_user_info(request)
        target_employee_id = request.GET.get('employee_id')
        
        # ===== AUTHORIZATION CHECK =====
        auth_svc = AuthorizationService()
        can_access = auth_svc.can_access_employee_record(
            user_role, user_id, target_employee_id
        )
        if not can_access:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # Get employee
        employee = Employee.objects.get(id=target_employee_id)
        
        profile_data = {
            'employee_id': str(employee.id),
            'full_name': f"{employee.first_name} {employee.last_name}",
            'email': employee.email,
            'phone': employee.phone,
            'department': employee.department,
            'job_title': employee.job_title,
            'date_of_birth': employee.date_of_birth.isoformat(),
            'hire_date': employee.hire_date.isoformat(),
            'address': employee.address,
            'city': employee.city,
        }
        
        return JsonResponse(profile_data)
        
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['PUT'])
def update_employee_profile(request):
    """
    PUT /api/employees/{employee_id}/profile
    
    Request body:
    {
        "phone": "9999999999",
        "address": "New Address",
        "city": "New City"
    }
    """
    try:
        user_id, user_role = extract_user_info(request)
        target_employee_id = request.GET.get('employee_id')
        
        # ===== AUTHORIZATION CHECK =====
        auth_svc = AuthorizationService()
        can_access = auth_svc.can_access_employee_record(
            user_role, user_id, target_employee_id
        )
        if not can_access:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # Get employee
        employee = Employee.objects.get(id=target_employee_id)
        
        # ===== SERVICE LAYER EXECUTION =====
        data = request.JSON
        
        # Build updates dict (only allowed fields)
        allowed_updates = {}
        if user_role == UserRole.EMPLOYEE:
            # Employees can only update certain fields
            for field in ['phone', 'address', 'city', 'postal_code']:
                if field in data:
                    allowed_updates[field] = data[field]
        else:
            # Admins can update more
            allowed_updates = data
        
        # ===== UPDATE DATABASE =====
        with transaction.atomic():
            for key, value in allowed_updates.items():
                if hasattr(employee, key):
                    setattr(employee, key, value)
            employee.save()
        
        return JsonResponse({
            'message': 'Profile updated',
            'employee_id': str(employee.id),
        })
        
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# URL CONFIGURATION (urls.py)
# ============================================================================

"""
# hrms/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Leave Management
    path('leave/apply', views.apply_leave, name='apply_leave'),
    path('leave/approve', views.approve_leave, name='approve_leave'),
    
    # Attendance
    path('attendance/check-in', views.check_in, name='check_in'),
    path('attendance/check-out', views.check_out, name='check_out'),
    
    # Payroll
    path('payroll/process', views.process_monthly_payroll, name='process_payroll'),
    path('payroll/slip', views.get_salary_slip, name='get_salary_slip'),
    
    # Profile
    path('employees/profile', views.get_employee_profile, name='get_profile'),
    path('employees/profile/update', views.update_employee_profile, name='update_profile'),
]
"""
