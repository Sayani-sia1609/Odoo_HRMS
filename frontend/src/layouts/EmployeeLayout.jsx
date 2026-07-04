import { useNavigate } from 'react-router-dom'
import { useHRMS } from '../hooks/useHRMS'
import DashboardLayout from './DashboardLayout'

const employeeLinks = [
  { to: '/employee/dashboard', label: 'Dashboard' },
  { to: '/employee/profile', label: 'Profile' },
  { to: '/employee/attendance', label: 'Attendance' },
  { to: '/employee/leave', label: 'Leave & Time-off' },
  { to: '/employee/payroll', label: 'Payroll' },
]

function EmployeeLayout() {
  const navigate = useNavigate()
  const { logout, currentEmployee, currentUser } = useHRMS()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <DashboardLayout
      title="Employee"
      links={employeeLinks}
      onLogout={handleLogout}
      profileName={currentEmployee?.fullName ?? currentUser?.fullName ?? 'Employee'}
      roleLabel="Employee"
    />
  )
}

export default EmployeeLayout
