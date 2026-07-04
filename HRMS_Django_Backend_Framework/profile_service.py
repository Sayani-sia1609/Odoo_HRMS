"""
Employee Profile Management Service
Core business logic for managing employee profiles and information.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
import re


class EmploymentStatus(Enum):
    """Employment status of employee."""
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    RESIGNED = "resigned"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class Department(Enum):
    """Company departments."""
    ENGINEERING = "engineering"
    PRODUCT = "product"
    SALES = "sales"
    MARKETING = "marketing"
    HR = "hr"
    FINANCE = "finance"
    OPERATIONS = "operations"


@dataclass
class ContactInfo:
    """Employee contact information."""
    email: str
    phone: str
    address: str
    city: str
    state: str
    postal_code: str
    country: str = "India"
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    
    def validate(self) -> tuple[bool, str]:
        """Validate contact information."""
        # Email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            return False, "Invalid email format"
        
        # Phone validation (basic)
        if not re.match(r'^\+?1?\d{10,13}$', self.phone.replace('-', '').replace(' ', '')):
            return False, "Invalid phone number"
        
        if not self.address or not self.city or not self.postal_code:
            return False, "Address details are incomplete"
        
        return True, ""


@dataclass
class PersonalInfo:
    """Employee personal information."""
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str  # "Male", "Female", "Other"
    marital_status: str  # "Single", "Married", etc.
    blood_group: Optional[str] = None
    nationality: str = "Indian"
    
    def get_full_name(self) -> str:
        """Get full name."""
        return f"{self.first_name} {self.last_name}"
    
    def get_age(self) -> int:
        """Calculate age from DOB."""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def validate(self) -> tuple[bool, str]:
        """Validate personal information."""
        if not self.first_name or not self.last_name:
            return False, "First and last name are required"
        
        if self.date_of_birth > date.today():
            return False, "DOB cannot be in future"
        
        if self.get_age() < 18:
            return False, "Employee must be 18 years or older"
        
        if self.get_age() > 70:
            return False, "Employee age seems invalid"
        
        return True, ""


@dataclass
class JobInfo:
    """Employee job details."""
    employee_id: str
    job_title: str
    department: Department
    manager_id: Optional[str]  # ID of reporting manager
    employment_type: str  # "Full-time", "Contract", etc.
    employment_status: EmploymentStatus = EmploymentStatus.ACTIVE
    hire_date: date = field(default_factory=date.today)
    location: str = "Head Office"
    
    def get_tenure_years(self) -> float:
        """Get employment tenure in years."""
        today = date.today()
        days = (today - self.hire_date).days
        return days / 365.25


@dataclass
class EducationRecord:
    """Education qualification record."""
    record_id: str
    degree: str  # "Bachelor", "Master", "PhD", etc.
    field_of_study: str
    institution: str
    graduation_year: int
    grade_gpa: Optional[str] = None


@dataclass
class Document:
    """Employee document (certificate, ID, etc.)."""
    document_id: str
    document_type: str  # "Aadhar", "PAN", "Passport", etc.
    document_number: str
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    uploaded_at: datetime = field(default_factory=datetime.now)


@dataclass
class EmployeeProfile:
    """Complete employee profile."""
    employee_id: str
    personal_info: PersonalInfo
    contact_info: ContactInfo
    job_info: JobInfo
    education_records: List[EducationRecord] = field(default_factory=list)
    documents: List[Document] = field(default_factory=list)
    profile_picture_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    updated_by: Optional[str] = None


class ProfileValidationService:
    """Validate employee profile data."""
    
    def validate_profile(self, profile: EmployeeProfile) -> tuple[bool, str]:
        """Validate complete profile."""
        # Validate personal info
        is_valid, error = profile.personal_info.validate()
        if not is_valid:
            return False, f"Personal info: {error}"
        
        # Validate contact info
        is_valid, error = profile.contact_info.validate()
        if not is_valid:
            return False, f"Contact info: {error}"
        
        # Validate job info
        if not profile.job_info.job_title:
            return False, "Job title is required"
        
        return True, ""
    
    def validate_employee_id_format(self, employee_id: str) -> tuple[bool, str]:
        """Validate employee ID format."""
        # Example: EMP-2024-0001
        pattern = r'^EMP-\d{4}-\d{4}$'
        if not re.match(pattern, employee_id):
            return False, "Invalid employee ID format"
        return True, ""


class ProfileManagementService:
    """Manage employee profiles."""
    
    def create_profile(self, profile: EmployeeProfile, admin_id: str) -> EmployeeProfile:
        """Create new employee profile."""
        validator = ProfileValidationService()
        is_valid, error = validator.validate_profile(profile)
        if not is_valid:
            raise ValueError(error)
        
        is_valid, error = validator.validate_employee_id_format(profile.employee_id)
        if not is_valid:
            raise ValueError(error)
        
        profile.created_at = datetime.now()
        profile.updated_at = datetime.now()
        profile.updated_by = admin_id
        
        return profile
    
    def update_profile(self, profile: EmployeeProfile, updates: Dict[str, Any],
                      requester_id: str, requester_role: str) -> EmployeeProfile:
        """
        Update employee profile with role-based restrictions.
        
        Employee can only update certain fields, Admin can update all.
        """
        restricted_fields = {'employee_id', 'created_at', 'job_info'}
        
        if requester_role == "employee":
            # Employees can only update personal contact info
            for field in updates:
                if field in restricted_fields:
                    raise PermissionError(f"Cannot update field: {field}")
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        profile.updated_at = datetime.now()
        profile.updated_by = requester_id
        
        return profile
    
    def edit_profile_picture(self, profile: EmployeeProfile,
                            picture_url: str) -> EmployeeProfile:
        """Update profile picture."""
        if not picture_url:
            raise ValueError("Picture URL cannot be empty")
        
        profile.profile_picture_url = picture_url
        profile.updated_at = datetime.now()
        
        return profile


class EducationService:
    """Manage employee education records."""
    
    def add_education(self, profile: EmployeeProfile,
                     degree: str, field: str, institution: str,
                     graduation_year: int, gpa: Optional[str] = None) -> Document:
        """Add education record to profile."""
        if graduation_year > date.today().year + 1:
            raise ValueError("Graduation year cannot be in far future")
        
        record = EducationRecord(
            record_id=f"edu_{len(profile.education_records) + 1}",
            degree=degree,
            field_of_study=field,
            institution=institution,
            graduation_year=graduation_year,
            grade_gpa=gpa,
        )
        
        profile.education_records.append(record)
        return record
    
    def remove_education(self, profile: EmployeeProfile, record_id: str) -> bool:
        """Remove education record."""
        profile.education_records = [
            r for r in profile.education_records if r.record_id != record_id
        ]
        return True


class DocumentService:
    """Manage employee documents."""
    
    VALID_DOCUMENT_TYPES = {
        'AADHAR', 'PAN', 'PASSPORT', 'DRIVING_LICENSE',
        'BIRTH_CERTIFICATE', 'DEGREE_CERTIFICATE', 'EMPLOYMENT_LETTER'
    }
    
    def add_document(self, profile: EmployeeProfile,
                    document_type: str, document_number: str,
                    issue_date: Optional[date] = None,
                    expiry_date: Optional[date] = None) -> Document:
        """Add document to profile."""
        if document_type.upper() not in self.VALID_DOCUMENT_TYPES:
            raise ValueError(f"Invalid document type: {document_type}")
        
        if expiry_date and expiry_date < date.today():
            raise ValueError("Document has expired")
        
        doc = Document(
            document_id=f"doc_{len(profile.documents) + 1}",
            document_type=document_type,
            document_number=document_number,
            issue_date=issue_date,
            expiry_date=expiry_date,
        )
        
        profile.documents.append(doc)
        return doc
    
    def verify_document_expiry(self, document: Document) -> tuple[bool, str]:
        """Check if document is valid (not expired)."""
        if document.expiry_date is None:
            return True, "No expiry date"
        
        if document.expiry_date < date.today():
            return False, f"Document expired on {document.expiry_date}"
        
        days_until_expiry = (document.expiry_date - date.today()).days
        if days_until_expiry < 30:
            return True, f"Warning: expires in {days_until_expiry} days"
        
        return True, "Valid"
    
    def get_expiring_documents(self, profile: EmployeeProfile,
                              days_threshold: int = 30) -> List[Document]:
        """Get documents expiring within threshold."""
        expiring = []
        today = date.today()
        threshold_date = today + timedelta(days=days_threshold)
        
        for doc in profile.documents:
            if doc.expiry_date and today <= doc.expiry_date <= threshold_date:
                expiring.append(doc)
        
        return expiring


class EmployeeDirectoryService:
    """Search and filter employees in the organization."""
    
    def search_employees(self, profiles: List[EmployeeProfile],
                        query: str) -> List[EmployeeProfile]:
        """Search employees by name or employee ID."""
        query_lower = query.lower()
        results = []
        
        for profile in profiles:
            if (query_lower in profile.personal_info.get_full_name().lower() or
                query_lower in profile.employee_id.lower() or
                query_lower in profile.contact_info.email.lower()):
                results.append(profile)
        
        return results
    
    def get_department_employees(self, profiles: List[EmployeeProfile],
                                department: Department) -> List[EmployeeProfile]:
        """Get all employees in a department."""
        return [
            p for p in profiles
            if p.job_info.department == department and
            p.job_info.employment_status == EmploymentStatus.ACTIVE
        ]
    
    def get_reporting_structure(self, profiles: List[EmployeeProfile],
                               manager_id: str) -> List[EmployeeProfile]:
        """Get all employees reporting to a manager."""
        return [
            p for p in profiles
            if p.job_info.manager_id == manager_id and
            p.job_info.employment_status == EmploymentStatus.ACTIVE
        ]
    
    def get_employees_by_location(self, profiles: List[EmployeeProfile],
                                 location: str) -> List[EmployeeProfile]:
        """Get employees at a specific location."""
        return [
            p for p in profiles
            if p.job_info.location == location
        ]


# Import statement for timedelta needed in DocumentService
from datetime import timedelta
