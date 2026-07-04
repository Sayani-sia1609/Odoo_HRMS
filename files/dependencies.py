"""
Shared FastAPI dependencies: current-user extraction and role-based
access control (RBAC), for use by any router in the project (profile,
attendance, leave, payroll, dashboard, etc.) — PRD 2: Admin vs Employee.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import RevokedToken, User, RoleEnum
from .security import decode_access_token

# tokenUrl just points Swagger UI's "Authorize" button at the login route.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    token_jti: str = payload.get("jti")
    if token_jti is None:
        raise credentials_exception

    is_revoked = db.query(RevokedToken).filter(RevokedToken.jti == token_jti).first()
    if is_revoked is not None:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    return user


def require_roles(*allowed_roles: RoleEnum):
    """
    Dependency factory for RBAC, e.g.:
        Depends(require_roles(RoleEnum.admin))
    """

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return role_checker


# Convenience shortcuts for other routers to import directly
get_current_admin = require_roles(RoleEnum.admin)
get_current_employee_or_admin = require_roles(RoleEnum.admin, RoleEnum.employee)
