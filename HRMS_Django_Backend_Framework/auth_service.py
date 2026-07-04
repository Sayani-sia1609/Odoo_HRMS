"""
Authentication and Authorization Service
Handles user authentication, role-based access, and permission checks.
"""

from functools import wraps
from enum import Enum
from typing import Callable, Optional, Any
from datetime import datetime, timedelta
import hashlib
import secrets


class UserRole(Enum):
    """Enum for user roles in the system."""
    ADMIN = "admin"
    HR_OFFICER = "hr_officer"
    EMPLOYEE = "employee"


class AuthenticationService:
    """
    Core authentication logic (decoupled from Django's ORM).
    Password hashing and token generation/validation.
    """

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """
        Hash password with salt. Returns (hashed_password, salt).
        In production, use bcrypt or argon2. This is placeholder.
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return hashed.hex(), salt

    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """Verify password against stored hash."""
        hashed, _ = AuthenticationService.hash_password(password, salt)
        return hashed == stored_hash

    @staticmethod
    def validate_email(email: str) -> bool:
        """Basic email validation."""
        return '@' in email and '.' in email.split('@')[1]

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """
        Validate password strength.
        Returns (is_valid, error_message).
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        if not any(c.isupper() for c in password):
            return False, "Password must contain uppercase letter"
        if not any(c.isdigit() for c in password):
            return False, "Password must contain digit"
        if not any(c in "!@#$%^&*" for c in password):
            return False, "Password must contain special character"
        return True, ""


class AuthorizationService:
    """
    Role-based access control (RBAC) logic.
    Manages permissions and role hierarchies.
    """

    ROLE_PERMISSIONS = {
        UserRole.ADMIN: {
            'view_all_employees',
            'manage_employees',
            'approve_leave',
            'view_payroll',
            'update_payroll',
            'manage_attendance',
            'view_attendance_all',
        },
        UserRole.HR_OFFICER: {
            'view_all_employees',
            'approve_leave',
            'view_payroll',
            'view_attendance_all',
        },
        UserRole.EMPLOYEE: {
            'view_own_profile',
            'edit_own_profile',
            'apply_for_leave',
            'view_own_attendance',
            'view_own_payroll',
        }
    }

    @classmethod
    def has_permission(cls, user_role: UserRole, permission: str) -> bool:
        """Check if a role has a specific permission."""
        return permission in cls.ROLE_PERMISSIONS.get(user_role, set())

    @classmethod
    def can_access_employee_record(cls, requester_role: UserRole, 
                                   requester_id: str, target_employee_id: str) -> bool:
        """
        Check if requester can access target employee's record.
        Employees can only view their own records.
        """
        if requester_role in [UserRole.ADMIN, UserRole.HR_OFFICER]:
            return True
        
        if requester_role == UserRole.EMPLOYEE:
            return requester_id == target_employee_id
        
        return False


def require_role(*allowed_roles: UserRole):
    """
    Decorator for requiring specific roles.
    Usage: @require_role(UserRole.ADMIN, UserRole.HR_OFFICER)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user_role from context (typically from request)
            user_role = kwargs.get('user_role')
            
            if not user_role or user_role not in allowed_roles:
                raise PermissionError(
                    f"This action requires one of: {[r.value for r in allowed_roles]}"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_permission(permission: str):
    """
    Decorator for requiring specific permission.
    Usage: @require_permission('approve_leave')
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_role = kwargs.get('user_role')
            
            if not user_role or not AuthorizationService.has_permission(user_role, permission):
                raise PermissionError(f"Permission required: {permission}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
