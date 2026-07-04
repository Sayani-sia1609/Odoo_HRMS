import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import AdminAttendancePage from '../pages/admin/AdminAttendancePage'
import AdminDashboardPage from '../pages/admin/AdminDashboardPage'
import AdminEmployeesPage from '../pages/admin/AdminEmployeesPage'
import AdminLeaveApprovalsPage from '../pages/admin/AdminLeaveApprovalsPage'
import AdminPayrollPage from '../pages/admin/AdminPayrollPage'
import LoginPage from '../pages/auth/LoginPage'
import SignupPage from '../pages/auth/SignupPage'
import EmployeeAttendancePage from '../pages/employee/EmployeeAttendancePage'
import EmployeeDashboardPage from '../pages/employee/EmployeeDashboardPage'
import EmployeeLeavePage from '../pages/employee/EmployeeLeavePage'
import EmployeePayrollPage from '../pages/employee/EmployeePayrollPage'
import EmployeeProfilePage from '../pages/employee/EmployeeProfilePage'
import AdminLayout from '../layouts/AdminLayout'
import EmployeeLayout from '../layouts/EmployeeLayout'
import ProtectedRoute from './ProtectedRoute'

function RootRedirect() {
  const { isAuthenticated, role } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (role === 'admin') {
    return <Navigate to="/admin/dashboard" replace />
  }

  return <Navigate to="/employee/dashboard" replace />
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<RootRedirect />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />

      <Route element={<ProtectedRoute allowedRole="employee" />}>
        <Route path="/employee" element={<EmployeeLayout />}>
          <Route path="dashboard" element={<EmployeeDashboardPage />} />
          <Route path="profile" element={<EmployeeProfilePage />} />
          <Route path="attendance" element={<EmployeeAttendancePage />} />
          <Route path="leave" element={<EmployeeLeavePage />} />
          <Route path="payroll" element={<EmployeePayrollPage />} />
        </Route>
      </Route>

      <Route element={<ProtectedRoute allowedRole="admin" />}>
        <Route path="/admin" element={<AdminLayout />}>
          <Route path="dashboard" element={<AdminDashboardPage />} />
          <Route path="employees" element={<AdminEmployeesPage />} />
          <Route path="attendance" element={<AdminAttendancePage />} />
          <Route path="leaves" element={<AdminLeaveApprovalsPage />} />
          <Route path="payroll" element={<AdminPayrollPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default AppRoutes
