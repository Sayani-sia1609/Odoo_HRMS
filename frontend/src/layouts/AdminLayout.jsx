import { useNavigate } from 'react-router-dom'
import { useHRMS } from '../hooks/useHRMS'
import DashboardLayout from './DashboardLayout'

const adminLinks = [
  { to: '/admin/dashboard', label: 'Dashboard' },
  { to: '/admin/employees', label: 'Employee List' },
  { to: '/admin/attendance', label: 'Attendance Records' },
  { to: '/admin/leaves', label: 'Leave Approvals' },
  { to: '/admin/payroll', label: 'Payroll Control' },
]

function AdminLayout() {
  const navigate = useNavigate()
  const { logout, currentUser } = useHRMS()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <DashboardLayout
      title="Admin / HR"
      links={adminLinks}
      onLogout={handleLogout}
      profileName={currentUser?.fullName ?? 'HR Admin'}
      roleLabel="Admin"
    />
  )
}

export default AdminLayout
