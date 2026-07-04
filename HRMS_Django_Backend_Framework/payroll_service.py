"""
Payroll Management Service
Core business logic for salary calculation, deductions, and payroll processing.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
from abc import ABC, abstractmethod


class DeductionType(Enum):
    """Types of salary deductions."""
    INCOME_TAX = "income_tax"
    PROVIDENT_FUND = "provident_fund"
    EMPLOYEE_INSURANCE = "employee_insurance"
    PROFESSIONAL_TAX = "professional_tax"
    LOAN_DEDUCTION = "loan_deduction"


class AllowanceType(Enum):
    """Types of salary allowances."""
    BASIC = "basic"
    DEARNESS_ALLOWANCE = "dearness_allowance"
    HOUSE_RENT_ALLOWANCE = "house_rent_allowance"
    CONVEYANCE = "conveyance"
    MEDICAL = "medical"
    SPECIAL_ALLOWANCE = "special_allowance"


@dataclass
class SalaryComponent:
    """Single salary component (earning or deduction)."""
    component_id: str
    name: str
    amount: float
    is_fixed: bool  # True if fixed, False if variable
    description: Optional[str] = None
    
    def validate(self) -> tuple[bool, str]:
        """Validate component values."""
        if self.amount < 0:
            return False, "Amount cannot be negative"
        return True, ""


@dataclass
class SalaryStructure:
    """Complete salary structure for an employee."""
    employee_id: str
    effective_date: date
    base_salary: float
    allowances: List[SalaryComponent] = field(default_factory=list)
    deductions: List[SalaryComponent] = field(default_factory=list)
    updated_at: datetime = field(default_factory=datetime.now)
    updated_by: Optional[str] = None
    
    def get_gross_salary(self) -> float:
        """Calculate gross salary (base + allowances)."""
        allowance_total = sum(a.amount for a in self.allowances)
        return self.base_salary + allowance_total
    
    def get_total_deductions(self) -> float:
        """Calculate total deductions."""
        return sum(d.amount for d in self.deductions)
    
    def get_net_salary(self) -> float:
        """Calculate net salary (gross - deductions)."""
        return self.get_gross_salary() - self.get_total_deductions()


@dataclass
class PayrollRecord:
    """Single month's payroll for an employee."""
    payroll_id: str
    employee_id: str
    salary_month: date  # First day of the month
    salary_structure: SalaryStructure
    
    # Actual values (may differ from structure if variable)
    actual_allowances: List[SalaryComponent] = field(default_factory=list)
    actual_deductions: List[SalaryComponent] = field(default_factory=list)
    
    # Adjustments
    bonus: float = 0.0
    incentive: float = 0.0
    arrears: float = 0.0
    
    # Attendance impact
    working_days_in_month: int = 0
    days_worked: int = 0
    leave_days: int = 0
    
    # Status
    is_finalized: bool = False
    finalized_at: Optional[datetime] = None
    finalized_by: Optional[str] = None
    
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_attendance_adjustment(self) -> float:
        """Calculate salary adjustment based on attendance."""
        if self.working_days_in_month == 0:
            return 0.0
        
        return (self.salary_structure.get_gross_salary() / self.working_days_in_month) * self.leave_days
    
    def get_gross_salary(self) -> float:
        """Calculate gross salary for this month."""
        # Use actual allowances if provided, else use structure
        allowances = self.actual_allowances if self.actual_allowances else self.salary_structure.allowances
        allowance_total = sum(a.amount for a in allowances)
        
        attendance_deduction = self.get_attendance_adjustment()
        
        gross = (self.salary_structure.base_salary + allowance_total - 
                attendance_deduction + self.bonus + self.incentive)
        
        return max(0, gross)  # Never negative
    
    def get_total_deductions(self) -> float:
        """Calculate total deductions for this month."""
        # Use actual deductions if provided, else use structure
        deductions = self.actual_deductions if self.actual_deductions else self.salary_structure.deductions
        return sum(d.amount for d in deductions)
    
    def get_net_salary(self) -> float:
        """Calculate net salary for this month."""
        return self.get_gross_salary() - self.get_total_deductions()


class PayrollCalculationService:
    """Core payroll calculation logic."""
    
    @staticmethod
    def calculate_income_tax(gross_salary: float) -> float:
        """
        Calculate income tax based on gross salary.
        Using simplified Indian tax brackets (example).
        Actual implementation would depend on jurisdiction and rules.
        """
        annual_gross = gross_salary * 12
        
        if annual_gross <= 250000:
            return 0
        elif annual_gross <= 500000:
            return (annual_gross - 250000) * 0.05 / 12
        elif annual_gross <= 1000000:
            return ((annual_gross - 500000) * 0.20 + 12500) / 12
        else:
            return ((annual_gross - 1000000) * 0.30 + 112500) / 12
    
    @staticmethod
    def calculate_provident_fund(gross_salary: float, employee_contribution_rate: float = 0.12) -> float:
        """Calculate provident fund deduction."""
        return gross_salary * employee_contribution_rate
    
    @staticmethod
    def calculate_professional_tax(gross_salary: float, state_rules: str = "standard") -> float:
        """Calculate professional tax (varies by state in India)."""
        annual_gross = gross_salary * 12
        
        # Standard rules
        if annual_gross <= 150000:
            return 0
        elif annual_gross <= 300000:
            return 200 / 12  # Approx per month
        else:
            return 500 / 12
    
    @staticmethod
    def generate_payroll(salary_structure: SalaryStructure,
                        working_days: int, days_worked: int,
                        bonus: float = 0.0) -> Dict[str, float]:
        """
        Generate payroll breakdown for a month.
        
        Returns dict with all components.
        """
        gross_salary = salary_structure.get_gross_salary()
        
        # Adjust for attendance
        leave_days = working_days - days_worked
        attendance_adjustment = (gross_salary / working_days) * leave_days if working_days > 0 else 0
        
        adjusted_gross = gross_salary - attendance_adjustment + bonus
        
        # Calculate deductions
        income_tax = PayrollCalculationService.calculate_income_tax(adjusted_gross)
        pf = PayrollCalculationService.calculate_provident_fund(adjusted_gross)
        prof_tax = PayrollCalculationService.calculate_professional_tax(adjusted_gross)
        
        total_deductions = income_tax + pf + prof_tax + sum(d.amount for d in salary_structure.deductions)
        
        net_salary = adjusted_gross - total_deductions
        
        return {
            'gross_salary': gross_salary,
            'attendance_adjustment': attendance_adjustment,
            'bonus': bonus,
            'adjusted_gross': adjusted_gross,
            'income_tax': income_tax,
            'provident_fund': pf,
            'professional_tax': prof_tax,
            'other_deductions': sum(d.amount for d in salary_structure.deductions),
            'total_deductions': total_deductions,
            'net_salary': max(0, net_salary),
        }


class SalaryStructureService:
    """Manage employee salary structures."""
    
    def create_salary_structure(self, employee_id: str, base_salary: float,
                               allowances: Dict[str, float],
                               admin_id: str) -> SalaryStructure:
        """Create new salary structure for an employee."""
        if base_salary < 0:
            raise ValueError("Base salary cannot be negative")
        
        allowance_components = [
            SalaryComponent(
                component_id=f"allowance_{i}",
                name=name,
                amount=amount,
                is_fixed=True
            )
            for i, (name, amount) in enumerate(allowances.items())
        ]
        
        # Default deductions
        deduction_components = [
            SalaryComponent(
                component_id="ded_income_tax",
                name="Income Tax",
                amount=0,  # Calculated dynamically
                is_fixed=False
            ),
            SalaryComponent(
                component_id="ded_pf",
                name="Provident Fund",
                amount=0,
                is_fixed=False
            ),
        ]
        
        structure = SalaryStructure(
            employee_id=employee_id,
            effective_date=date.today(),
            base_salary=base_salary,
            allowances=allowance_components,
            deductions=deduction_components,
            updated_by=admin_id,
        )
        
        return structure
    
    def update_salary_structure(self, structure: SalaryStructure,
                               new_base_salary: Optional[float] = None,
                               admin_id: Optional[str] = None) -> SalaryStructure:
        """Update salary structure."""
        if new_base_salary is not None:
            if new_base_salary < 0:
                raise ValueError("Base salary cannot be negative")
            structure.base_salary = new_base_salary
        
        structure.updated_at = datetime.now()
        structure.updated_by = admin_id
        structure.effective_date = date.today()
        
        return structure
    
    def get_salary_history(self, employee_id: str,
                          structures: List[SalaryStructure]) -> List[SalaryStructure]:
        """Get salary structure change history for an employee."""
        return [s for s in structures if s.employee_id == employee_id]


class PayrollFinalizationService:
    """Handle payroll finalization and approval workflow."""
    
    def finalize_payroll(self, payroll: PayrollRecord, admin_id: str) -> PayrollRecord:
        """
        Finalize payroll for a month.
        Once finalized, payroll is locked for further changes.
        """
        if payroll.is_finalized:
            raise ValueError("Payroll already finalized")
        
        payroll.is_finalized = True
        payroll.finalized_at = datetime.now()
        payroll.finalized_by = admin_id
        
        return payroll
    
    def can_modify_payroll(self, payroll: PayrollRecord) -> bool:
        """Check if payroll can still be modified."""
        return not payroll.is_finalized
    
    def revert_finalization(self, payroll: PayrollRecord, admin_id: str) -> PayrollRecord:
        """Revert payroll finalization (admin only)."""
        payroll.is_finalized = False
        payroll.finalized_at = None
        payroll.finalized_by = None
        return payroll


class PayrollReportService:
    """Generate payroll reports and summaries."""
    
    def get_salary_slip(self, payroll: PayrollRecord) -> Dict[str, Any]:
        """Generate salary slip for an employee."""
        gross = payroll.get_gross_salary()
        deductions = payroll.get_total_deductions()
        net = payroll.get_net_salary()
        
        return {
            'payroll_id': payroll.payroll_id,
            'employee_id': payroll.employee_id,
            'salary_month': payroll.salary_month.strftime('%B %Y'),
            'earnings': {
                'base_salary': payroll.salary_structure.base_salary,
                'allowances': [
                    {'name': a.name, 'amount': a.amount}
                    for a in (payroll.actual_allowances or payroll.salary_structure.allowances)
                ],
                'bonus': payroll.bonus,
                'incentive': payroll.incentive,
                'gross_salary': gross,
            },
            'deductions': [
                {'name': d.name, 'amount': d.amount}
                for d in (payroll.actual_deductions or payroll.salary_structure.deductions)
            ],
            'total_deductions': deductions,
            'net_salary': net,
            'attendance': {
                'working_days': payroll.working_days_in_month,
                'days_worked': payroll.days_worked,
                'leave_days': payroll.leave_days,
            },
        }
    
    def get_payroll_summary(self, payrolls: List[PayrollRecord],
                           start_month: date, end_month: date) -> Dict[str, Any]:
        """Get payroll summary across multiple months."""
        relevant_payrolls = [
            p for p in payrolls
            if start_month <= p.salary_month <= end_month
        ]
        
        if not relevant_payrolls:
            return {'message': 'No payroll records found'}
        
        total_gross = sum(p.get_gross_salary() for p in relevant_payrolls)
        total_deductions = sum(p.get_total_deductions() for p in relevant_payrolls)
        total_net = sum(p.get_net_salary() for p in relevant_payrolls)
        
        return {
            'period': f"{start_month.strftime('%b %Y')} to {end_month.strftime('%b %Y')}",
            'months_covered': len(relevant_payrolls),
            'total_gross': total_gross,
            'total_deductions': total_deductions,
            'total_net': total_net,
            'average_monthly_net': total_net / len(relevant_payrolls),
        }
