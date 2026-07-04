"""
Lightweight dashboard summary endpoints (used for the quick-access cards
on the Employee and Admin dashboards).
"""
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Attendance, Leave, LeaveStatusEnum, AttendanceStatusEnum
from app.dependencies import get_current_user, get_current_admin

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/employee")
def employee_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today_record = db.query(Attendance).filter(
        Attendance.user_id == current_user.id, Attendance.date == date.today()
    ).first()

    pending_leaves = db.query(Leave).filter(
        Leave.user_id == current_user.id, Leave.status == LeaveStatusEnum.pending
    ).count()

    return {
        "employee_id": current_user.employee_id,
        "today_attendance_status": today_record.status if today_record else None,
        "pending_leave_requests": pending_leaves,
    }


@router.get("/admin")
def admin_dashboard(current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    total_employees = db.query(User).count()
    pending_leaves = db.query(Leave).filter(Leave.status == LeaveStatusEnum.pending).count()
    present_today = db.query(Attendance).filter(
        Attendance.date == date.today(), Attendance.status == AttendanceStatusEnum.present
    ).count()

    return {
        "total_employees": total_employees,
        "pending_leave_requests": pending_leaves,
        "present_today": present_today,
    }
