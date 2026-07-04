"""
Attendance Management Service
Core business logic for tracking, validating, and reporting attendance.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict


class AttendanceStatus(Enum):
    """Status of attendance for a day."""
    PRESENT = "present"
    ABSENT = "absent"
    HALF_DAY = "half_day"
    LEAVE = "leave"
    HOLIDAY = "holiday"
    WEEKEND = "weekend"


@dataclass
class AttendanceRecord:
    """Single day's attendance record."""
    employee_id: str
    date: date
    status: AttendanceStatus
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    remarks: Optional[str] = None
    marked_by: Optional[str] = None  # Admin who marked attendance
    marked_at: Optional[datetime] = None
    
    def get_hours_worked(self) -> Optional[float]:
        """Calculate hours worked if check-in/out times exist."""
        if not self.check_in_time or not self.check_out_time:
            return None
        
        # Convert times to datetime for calculation
        today = datetime.combine(self.date, self.check_in_time)
        checkout_time = datetime.combine(self.date, self.check_out_time)
        
        if checkout_time < today:
            # Handle case where checkout is next day
            checkout_time += timedelta(days=1)
        
        duration = checkout_time - today
        return duration.total_seconds() / 3600


class AttendanceValidationService:
    """Validates attendance records against business rules."""
    
    WORKING_HOURS_START = time(9, 0)  # 9 AM
    WORKING_HOURS_END = time(18, 0)   # 6 PM
    MIN_WORKING_HOURS = 8.0
    LATE_THRESHOLD_MINUTES = 15
    
    def validate_check_in(self, check_in_time: time) -> tuple[bool, str]:
        """Validate check-in time."""
        if check_in_time > self.WORKING_HOURS_END:
            return False, "Check-in time is after working hours"
        return True, ""
    
    def validate_check_out(self, check_in_time: time, check_out_time: time) -> tuple[bool, str]:
        """Validate check-out time relative to check-in."""
        if check_out_time <= check_in_time:
            return False, "Check-out time must be after check-in time"
        
        if check_out_time < self.WORKING_HOURS_START:
            return False, "Check-out time is before working hours start"
        
        return True, ""
    
    def is_late(self, check_in_time: time) -> bool:
        """Check if check-in is late."""
        late_time = (datetime.combine(date.today(), self.WORKING_HOURS_START) +
                    timedelta(minutes=self.LATE_THRESHOLD_MINUTES)).time()
        return check_in_time > late_time
    
    def is_early_departure(self, check_out_time: time) -> bool:
        """Check if employee left early."""
        return check_out_time < self.WORKING_HOURS_END
    
    def validate_attendance_date(self, attendance_date: date) -> tuple[bool, str]:
        """Validate that attendance can be marked for this date."""
        today = date.today()
        
        if attendance_date > today:
            return False, "Cannot mark attendance for future dates"
        
        # Can mark attendance up to 30 days in the past
        if (today - attendance_date).days > 30:
            return False, "Cannot mark attendance for dates older than 30 days"
        
        return True, ""


class AttendanceTrackingService:
    """Core attendance tracking logic."""
    
    def check_in(self, employee_id: str, check_in_time: time) -> AttendanceRecord:
        """Record employee check-in."""
        validation_service = AttendanceValidationService()
        is_valid, error = validation_service.validate_check_in(check_in_time)
        
        if not is_valid:
            raise ValueError(error)
        
        return AttendanceRecord(
            employee_id=employee_id,
            date=date.today(),
            status=AttendanceStatus.PRESENT,
            check_in_time=check_in_time,
            marked_at=datetime.now(),
        )
    
    def check_out(self, attendance_record: AttendanceRecord, 
                 check_out_time: time) -> AttendanceRecord:
        """Record employee check-out."""
        validation_service = AttendanceValidationService()
        is_valid, error = validation_service.validate_check_out(
            attendance_record.check_in_time,
            check_out_time
        )
        
        if not is_valid:
            raise ValueError(error)
        
        attendance_record.check_out_time = check_out_time
        
        # Determine if it's a full day or half day based on hours worked
        hours = attendance_record.get_hours_worked()
        if hours and hours < validation_service.MIN_WORKING_HOURS:
            attendance_record.status = AttendanceStatus.HALF_DAY
        
        return attendance_record
    
    def mark_attendance(self, employee_id: str, attendance_date: date,
                       status: AttendanceStatus, admin_id: str,
                       remarks: Optional[str] = None) -> AttendanceRecord:
        """
        Admin marks attendance for an employee.
        Used for manual corrections or bulk marking.
        """
        validation_service = AttendanceValidationService()
        is_valid, error = validation_service.validate_attendance_date(attendance_date)
        
        if not is_valid:
            raise ValueError(error)
        
        return AttendanceRecord(
            employee_id=employee_id,
            date=attendance_date,
            status=status,
            marked_by=admin_id,
            marked_at=datetime.now(),
            remarks=remarks,
        )


class AttendanceAnalyticsService:
    """Generate attendance reports and analytics."""
    
    def get_daily_attendance(self, attendance_records: List[AttendanceRecord],
                            target_date: date) -> Dict[str, AttendanceStatus]:
        """Get attendance status for all employees on a specific date."""
        daily = {}
        for record in attendance_records:
            if record.date == target_date:
                daily[record.employee_id] = record.status
        return daily
    
    def get_weekly_attendance(self, attendance_records: List[AttendanceRecord],
                             start_date: date) -> Dict[str, List[AttendanceRecord]]:
        """Get attendance records for a week, grouped by employee."""
        end_date = start_date + timedelta(days=6)
        weekly = defaultdict(list)
        
        for record in attendance_records:
            if start_date <= record.date <= end_date:
                weekly[record.employee_id].append(record)
        
        return dict(weekly)
    
    def get_monthly_attendance(self, attendance_records: List[AttendanceRecord],
                              year: int, month: int) -> Dict[str, List[AttendanceRecord]]:
        """Get attendance records for a month, grouped by employee."""
        monthly = defaultdict(list)
        
        for record in attendance_records:
            if record.date.year == year and record.date.month == month:
                monthly[record.employee_id].append(record)
        
        return dict(monthly)
    
    def get_attendance_summary(self, employee_id: str,
                              attendance_records: List[AttendanceRecord],
                              year: int = None, month: int = None) -> Dict[str, Any]:
        """Get attendance summary for an employee."""
        if year is None:
            year = date.today().year
        if month is None:
            month = date.today().month
        
        summary = {
            'employee_id': employee_id,
            'year': year,
            'month': month,
            'present': 0,
            'absent': 0,
            'half_day': 0,
            'leave': 0,
            'holiday': 0,
            'weekend': 0,
        }
        
        for record in attendance_records:
            if (record.employee_id == employee_id and
                record.date.year == year and
                record.date.month == month):
                
                status_key = record.status.value
                if status_key in summary:
                    summary[status_key] += 1
        
        summary['total_working_days'] = (
            summary['present'] + summary['half_day']
        )
        
        return summary
    
    def get_attendance_percentage(self, employee_id: str,
                                 attendance_records: List[AttendanceRecord],
                                 year: int = None, month: int = None) -> float:
        """Calculate attendance percentage for an employee."""
        summary = self.get_attendance_summary(employee_id, attendance_records, year, month)
        
        working_days = sum([
            summary['present'],
            summary['absent'],
            summary['half_day'],
        ])
        
        if working_days == 0:
            return 0.0
        
        attendance_days = summary['present'] + (summary['half_day'] * 0.5)
        return (attendance_days / working_days) * 100
    
    def identify_chronic_absentees(self, attendance_records: List[AttendanceRecord],
                                  threshold_percentage: float = 75.0) -> List[str]:
        """Identify employees below attendance threshold."""
        employee_ids = set(r.employee_id for r in attendance_records)
        chronic_absentees = []
        
        for emp_id in employee_ids:
            percentage = self.get_attendance_percentage(emp_id, attendance_records)
            if percentage < threshold_percentage:
                chronic_absentees.append(emp_id)
        
        return chronic_absentees


class AttendanceReportService:
    """Generate formatted reports for different stakeholders."""
    
    def get_employee_view(self, employee_id: str,
                         attendance_records: List[AttendanceRecord],
                         year: int = None, month: int = None) -> Dict[str, Any]:
        """Format attendance data for employee view (own attendance only)."""
        analytics = AttendanceAnalyticsService()
        summary = analytics.get_attendance_summary(employee_id, attendance_records, year, month)
        percentage = analytics.get_attendance_percentage(employee_id, attendance_records, year, month)
        
        return {
            'summary': summary,
            'attendance_percentage': round(percentage, 2),
            'records': [
                {
                    'date': r.date.isoformat(),
                    'status': r.status.value,
                    'check_in': r.check_in_time.isoformat() if r.check_in_time else None,
                    'check_out': r.check_out_time.isoformat() if r.check_out_time else None,
                    'hours_worked': round(r.get_hours_worked(), 2) if r.get_hours_worked() else None,
                }
                for r in attendance_records
                if r.employee_id == employee_id and
                (year is None or r.date.year == year) and
                (month is None or r.date.month == month)
            ]
        }
    
    def get_admin_view(self, attendance_records: List[AttendanceRecord],
                      year: int = None, month: int = None) -> Dict[str, Any]:
        """Format attendance data for admin view (all employees)."""
        analytics = AttendanceAnalyticsService()
        employee_ids = set(r.employee_id for r in attendance_records)
        
        return {
            'total_employees': len(employee_ids),
            'by_employee': {
                emp_id: analytics.get_attendance_summary(emp_id, attendance_records, year, month)
                for emp_id in employee_ids
            },
            'chronic_absentees': analytics.identify_chronic_absentees(attendance_records),
        }
