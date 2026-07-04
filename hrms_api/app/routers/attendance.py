"""
Attendance tracking routes (check-in/out, daily & weekly views).
"""
from datetime import date, timedelta, datetime as dt
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Attendance, AttendanceStatusEnum
from app.schemas import AttendanceOut, CheckInRequest, CheckOutRequest, AttendanceManualCreate
from app.dependencies import get_current_user, get_current_admin

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("/checkin", response_model=AttendanceOut, status_code=status.HTTP_201_CREATED)
def check_in(
    payload: CheckInRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today()
    record = db.query(Attendance).filter(
        Attendance.user_id == current_user.id, Attendance.date == today
    ).first()

    if record and record.check_in:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already checked in today")

    check_in_time = payload.check_in_time or dt.now().time()

    if not record:
        record = Attendance(
            user_id=current_user.id,
            date=today,
            check_in=check_in_time,
            status=AttendanceStatusEnum.present,
        )
        db.add(record)
    else:
        record.check_in = check_in_time
        record.status = AttendanceStatusEnum.present

    db.commit()
    db.refresh(record)
    return record


@router.post("/checkout", response_model=AttendanceOut)
def check_out(
    payload: CheckOutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today()
    record = db.query(Attendance).filter(
        Attendance.user_id == current_user.id, Attendance.date == today
    ).first()

    if not record or not record.check_in:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You must check in before checking out")

    if record.check_out:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already checked out today")

    record.check_out = payload.check_out_time or dt.now().time()
    db.commit()
    db.refresh(record)
    return record


@router.get("/me", response_model=List[AttendanceOut])
def get_my_attendance(
    view: str = Query("weekly", pattern="^(daily|weekly|monthly)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today()
    if view == "daily":
        start = today
    elif view == "weekly":
        start = today - timedelta(days=7)
    else:  # monthly
        start = today - timedelta(days=30)

    records = (
        db.query(Attendance)
        .filter(Attendance.user_id == current_user.id, Attendance.date >= start, Attendance.date <= today)
        .order_by(Attendance.date.desc())
        .all()
    )
    return records


@router.get("/{user_id}", response_model=List[AttendanceOut])
def get_employee_attendance(
    user_id: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    query = db.query(Attendance).filter(Attendance.user_id == user_id)
    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)

    return query.order_by(Attendance.date.desc()).all()


@router.get("/", response_model=List[AttendanceOut])
def get_all_attendance(
    target_date: Optional[date] = Query(None, description="Filter by a specific date"),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Attendance)
    if target_date:
        query = query.filter(Attendance.date == target_date)
    return query.order_by(Attendance.date.desc()).all()


@router.post("/{user_id}/manual", response_model=AttendanceOut, status_code=status.HTTP_201_CREATED)
def set_attendance_manually(
    user_id: str,
    payload: AttendanceManualCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Admin/HR can log or correct an employee's attendance for a given date."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    record = db.query(Attendance).filter(
        Attendance.user_id == user_id, Attendance.date == payload.date
    ).first()

    if not record:
        record = Attendance(user_id=user_id, date=payload.date)
        db.add(record)

    record.status = payload.status
    record.check_in = payload.check_in
    record.check_out = payload.check_out

    db.commit()
    db.refresh(record)
    return record
