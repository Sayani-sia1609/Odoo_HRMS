"""
Payroll / salary management routes.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Payroll
from app.schemas import PayrollOut, PayrollUpdate
from app.dependencies import get_current_user, get_current_admin

router = APIRouter(prefix="/payroll", tags=["Payroll"])


def _get_or_create_payroll(db: Session, user_id: str) -> Payroll:
    payroll = db.query(Payroll).filter(Payroll.user_id == user_id).first()
    if not payroll:
        payroll = Payroll(user_id=user_id)
        db.add(payroll)
        db.commit()
        db.refresh(payroll)
    return payroll


@router.get("/me", response_model=PayrollOut)
def get_my_payroll(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    payroll = _get_or_create_payroll(db, current_user.id)
    return payroll


@router.get("/", response_model=List[PayrollOut])
def list_all_payroll(current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [_get_or_create_payroll(db, user.id) for user in users]


@router.get("/{user_id}", response_model=PayrollOut)
def get_employee_payroll(
    user_id: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return _get_or_create_payroll(db, user_id)


@router.put("/{user_id}", response_model=PayrollOut)
def update_employee_payroll(
    user_id: str,
    payload: PayrollUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    payroll = _get_or_create_payroll(db, user_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(payroll, field, value)

    db.commit()
    db.refresh(payroll)
    return payroll
