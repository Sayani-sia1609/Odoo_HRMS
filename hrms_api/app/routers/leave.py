"""
Leave / time-off management routes.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Leave, LeaveStatusEnum
from app.schemas import LeaveApply, LeaveOut, LeaveDecision
from app.dependencies import get_current_user, get_current_admin

router = APIRouter(prefix="/leave", tags=["Leave"])


@router.post("/apply", response_model=LeaveOut, status_code=status.HTTP_201_CREATED)
def apply_for_leave(
    payload: LeaveApply,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_date cannot be before start_date")

    leave = Leave(
        user_id=current_user.id,
        leave_type=payload.leave_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        remarks=payload.remarks,
        status=LeaveStatusEnum.pending,
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return leave


@router.get("/me", response_model=List[LeaveOut])
def get_my_leaves(
    status_filter: Optional[LeaveStatusEnum] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Leave).filter(Leave.user_id == current_user.id)
    if status_filter:
        query = query.filter(Leave.status == status_filter)
    return query.order_by(Leave.created_at.desc()).all()


@router.delete("/{leave_id}", status_code=status.HTTP_200_OK)
def cancel_my_leave(
    leave_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    leave = db.query(Leave).filter(Leave.id == leave_id, Leave.user_id == current_user.id).first()
    if not leave:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")

    if leave.status != LeaveStatusEnum.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending requests can be cancelled")

    db.delete(leave)
    db.commit()
    return {"message": "Leave request cancelled"}


@router.get("/", response_model=List[LeaveOut])
def get_all_leaves(
    status_filter: Optional[LeaveStatusEnum] = Query(None, alias="status"),
    user_id: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Leave)
    if status_filter:
        query = query.filter(Leave.status == status_filter)
    if user_id:
        query = query.filter(Leave.user_id == user_id)
    return query.order_by(Leave.created_at.desc()).all()


@router.put("/{leave_id}/decision", response_model=LeaveOut)
def decide_leave(
    leave_id: str,
    payload: LeaveDecision,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if payload.status not in (LeaveStatusEnum.approved, LeaveStatusEnum.rejected):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="status must be 'approved' or 'rejected'",
        )

    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")

    leave.status = payload.status
    leave.admin_comment = payload.admin_comment
    leave.decided_by = current_admin.id
    leave.decided_at = datetime.utcnow()

    db.commit()
    db.refresh(leave)
    return leave
