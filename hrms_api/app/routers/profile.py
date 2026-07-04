"""
Employee profile management routes.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Profile
from app.schemas import (
    EmployeeProfileOut,
    ProfileUpdateEmployee,
    ProfileUpdateAdmin,
)
from app.dependencies import get_current_user, get_current_admin

router = APIRouter(prefix="/profile", tags=["Profile"])


def _get_or_create_profile(db: Session, user_id: str) -> Profile:
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        profile = Profile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("/me", response_model=EmployeeProfileOut)
def get_my_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = _get_or_create_profile(db, current_user.id)
    return EmployeeProfileOut(user=current_user, profile=profile)


@router.put("/me", response_model=EmployeeProfileOut)
def update_my_profile(
    payload: ProfileUpdateEmployee,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = _get_or_create_profile(db, current_user.id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return EmployeeProfileOut(user=current_user, profile=profile)


@router.get("/", response_model=List[EmployeeProfileOut])
def list_all_employees(current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    users = db.query(User).all()
    result = []
    for user in users:
        profile = db.query(Profile).filter(Profile.user_id == user.id).first()
        result.append(EmployeeProfileOut(user=user, profile=profile))
    return result


@router.get("/{user_id}", response_model=EmployeeProfileOut)
def get_employee_profile(
    user_id: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    profile = _get_or_create_profile(db, user_id)
    return EmployeeProfileOut(user=user, profile=profile)


@router.put("/{user_id}", response_model=EmployeeProfileOut)
def update_employee_profile(
    user_id: str,
    payload: ProfileUpdateAdmin,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    profile = _get_or_create_profile(db, user_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return EmployeeProfileOut(user=user, profile=profile)
