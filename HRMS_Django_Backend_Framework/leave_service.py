"""
Leave Management Service
Core business logic for leave applications, approvals, and tracking.
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod


class LeaveType(Enum):
    """Types of leave available."""
    PAID_LEAVE = "paid_leave"
    SICK_LEAVE = "sick_leave"
    UNPAID_LEAVE = "unpaid_leave"
    CASUAL_LEAVE = "casual_leave"


class LeaveStatus(Enum):
    """Status of a leave request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass
class LeaveRequest:
    """Data structure for a leave request."""
    request_id: str
    employee_id: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    status: LeaveStatus
    remarks: str
    created_at: datetime
    approver_id: Optional[str] = None
    approval_comments: Optional[str] = None
    approved_at: Optional[datetime] = None

    def get_duration_days(self) -> int:
        """Calculate number of days for the leave."""
        return (self.end_date - self.start_date).days + 1


class LeaveBalanceStrategy(ABC):
    """
    Strategy pattern for calculating leave balance.
    Different organizations may have different leave policies.
    """
    
    @abstractmethod
    def get_annual_allocation(self) -> int:
        """Get annual leave allocation for this type."""
        pass
    
    @abstractmethod
    def can_apply(self, used_days: int) -> bool:
        """Check if employee can apply for more leave."""
        pass
    
    @abstractmethod
    def calculate_carryforward(self, unused_days: int) -> int:
        """Calculate carryforward balance to next year."""
        pass


class PaidLeaveStrategy(LeaveBalanceStrategy):
    """Paid leave policy: 20 days/year, max 5 carryforward."""
    
    ANNUAL_ALLOCATION = 20
    MAX_CARRYFORWARD = 5
    
    def get_annual_allocation(self) -> int:
        return self.ANNUAL_ALLOCATION
    
    def can_apply(self, used_days: int) -> bool:
        return used_days < self.ANNUAL_ALLOCATION
    
    def calculate_carryforward(self, unused_days: int) -> int:
        return min(unused_days, self.MAX_CARRYFORWARD)


class SickLeaveStrategy(LeaveBalanceStrategy):
    """Sick leave policy: 12 days/year, no carryforward."""
    
    ANNUAL_ALLOCATION = 12
    
    def get_annual_allocation(self) -> int:
        return self.ANNUAL_ALLOCATION
    
    def can_apply(self, used_days: int) -> bool:
        return used_days < self.ANNUAL_ALLOCATION
    
    def calculate_carryforward(self, unused_days: int) -> int:
        return 0  # No carryforward for sick leave


class UnpaidLeaveStrategy(LeaveBalanceStrategy):
    """Unpaid leave: unlimited, no allocation."""
    
    def get_annual_allocation(self) -> int:
        return 999  # Effectively unlimited
    
    def can_apply(self, used_days: int) -> bool:
        return True
    
    def calculate_carryforward(self, unused_days: int) -> int:
        return 0


class LeaveBalanceService:
    """Manages employee leave balances and allocations."""
    
    LEAVE_STRATEGIES = {
        LeaveType.PAID_LEAVE: PaidLeaveStrategy(),
        LeaveType.SICK_LEAVE: SickLeaveStrategy(),
        LeaveType.UNPAID_LEAVE: UnpaidLeaveStrategy(),
        LeaveType.CASUAL_LEAVE: PaidLeaveStrategy(),  # Same as paid
    }
    
    def get_strategy(self, leave_type: LeaveType) -> LeaveBalanceStrategy:
        """Get the appropriate strategy for a leave type."""
        return self.LEAVE_STRATEGIES[leave_type]
    
    def get_balance(self, employee_id: str, leave_type: LeaveType, 
                   used_days: int) -> int:
        """
        Calculate remaining balance for an employee.
        Returns days available.
        """
        strategy = self.get_strategy(leave_type)
        allocated = strategy.get_annual_allocation()
        return max(0, allocated - used_days)
    
    def can_apply_leave(self, employee_id: str, leave_type: LeaveType,
                       requested_days: int, used_days: int) -> tuple[bool, str]:
        """
        Check if employee can apply for leave.
        Returns (can_apply, reason_if_not).
        """
        strategy = self.get_strategy(leave_type)
        total_after_request = used_days + requested_days
        
        if not strategy.can_apply(total_after_request):
            available = strategy.get_annual_allocation() - used_days
            return False, f"Insufficient balance. Available: {available} days"
        
        return True, ""


class LeaveValidationService:
    """Validates leave requests for business rules."""
    
    MIN_ADVANCE_NOTICE_DAYS = 2
    MAX_CONTINUOUS_LEAVE_DAYS = 30
    
    def validate_dates(self, start_date: date, end_date: date) -> tuple[bool, str]:
        """Validate leave date range."""
        if start_date > end_date:
            return False, "Start date cannot be after end date"
        
        today = date.today()
        if start_date < today:
            return False, "Cannot apply for past dates"
        
        days_until_leave = (start_date - today).days
        if days_until_leave < self.MIN_ADVANCE_NOTICE_DAYS and start_date != today:
            return False, f"Leave must be applied {self.MIN_ADVANCE_NOTICE_DAYS} days in advance"
        
        duration = (end_date - start_date).days + 1
        if duration > self.MAX_CONTINUOUS_LEAVE_DAYS:
            return False, f"Cannot apply for more than {self.MAX_CONTINUOUS_LEAVE_DAYS} continuous days"
        
        return True, ""
    
    def check_overlap(self, employee_id: str, start_date: date, end_date: date,
                     existing_leaves: List[LeaveRequest]) -> tuple[bool, str]:
        """Check if requested dates overlap with existing approved leaves."""
        for leave in existing_leaves:
            if leave.status != LeaveStatus.APPROVED:
                continue
            
            # Check for overlap: request overlaps if it's not entirely before or after
            if not (end_date < leave.start_date or start_date > leave.end_date):
                return False, f"Overlaps with existing leave ({leave.start_date} to {leave.end_date})"
        
        return True, ""


class LeaveApprovalService:
    """Handles leave approval workflow."""
    
    def approve_leave(self, leave_request: LeaveRequest, approver_id: str,
                     comments: Optional[str] = None) -> LeaveRequest:
        """
        Approve a leave request.
        In real system, this would trigger notifications and update DB.
        """
        if leave_request.status != LeaveStatus.PENDING:
            raise ValueError(f"Cannot approve leave with status: {leave_request.status}")
        
        leave_request.status = LeaveStatus.APPROVED
        leave_request.approver_id = approver_id
        leave_request.approval_comments = comments
        leave_request.approved_at = datetime.now()
        
        return leave_request
    
    def reject_leave(self, leave_request: LeaveRequest, approver_id: str,
                    comments: str) -> LeaveRequest:
        """Reject a leave request with comments."""
        if leave_request.status != LeaveStatus.PENDING:
            raise ValueError(f"Cannot reject leave with status: {leave_request.status}")
        
        leave_request.status = LeaveStatus.REJECTED
        leave_request.approver_id = approver_id
        leave_request.approval_comments = comments
        leave_request.approved_at = datetime.now()
        
        return leave_request
    
    def cancel_leave(self, leave_request: LeaveRequest) -> LeaveRequest:
        """Cancel an approved leave (employee initiated)."""
        if leave_request.status != LeaveStatus.APPROVED:
            raise ValueError(f"Can only cancel approved leaves")
        
        today = date.today()
        if leave_request.start_date <= today:
            raise ValueError("Cannot cancel ongoing or past leave")
        
        leave_request.status = LeaveStatus.CANCELLED
        return leave_request
    
    def get_pending_approvals(self, approver_id: str, 
                            leaves: List[LeaveRequest]) -> List[LeaveRequest]:
        """Get all pending leave approvals for an approver."""
        return [l for l in leaves if l.status == LeaveStatus.PENDING]


class LeaveReportService:
    """Generate leave reports and analytics."""
    
    def get_employee_leave_summary(self, employee_id: str,
                                  leaves: List[LeaveRequest],
                                  year: int = None) -> Dict[str, Any]:
        """Get leave summary for an employee in a year."""
        if year is None:
            year = date.today().year
        
        summary = {
            'year': year,
            'by_type': {},
            'total_approved': 0,
            'total_pending': 0,
            'total_rejected': 0,
        }
        
        for leave_type in LeaveType:
            summary['by_type'][leave_type.value] = {
                'approved': 0,
                'pending': 0,
                'rejected': 0,
            }
        
        for leave in leaves:
            if leave.employee_id != employee_id:
                continue
            if leave.start_date.year != year:
                continue
            
            type_key = leave.leave_type.value
            status_key = leave.status.value
            
            if status_key in summary['by_type'][type_key]:
                summary['by_type'][type_key][status_key] += leave.get_duration_days()
            
            if leave.status == LeaveStatus.APPROVED:
                summary['total_approved'] += leave.get_duration_days()
            elif leave.status == LeaveStatus.PENDING:
                summary['total_pending'] += leave.get_duration_days()
            elif leave.status == LeaveStatus.REJECTED:
                summary['total_rejected'] += leave.get_duration_days()
        
        return summary
    
    def get_department_leave_summary(self, department_id: str,
                                    leaves: List[LeaveRequest]) -> Dict[str, Any]:
        """Get aggregated leave report for a department."""
        # This would join with employee records to filter by department
        return {
            'department_id': department_id,
            'total_approved_days': sum(
                l.get_duration_days() 
                for l in leaves 
                if l.status == LeaveStatus.APPROVED
            ),
            'pending_count': len([l for l in leaves if l.status == LeaveStatus.PENDING]),
        }
