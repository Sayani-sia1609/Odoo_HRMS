import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import AdminLayout from '../layouts/AdminLayout'
import EmployeeLayout from '../layouts/EmployeeLayout'
import ProtectedRoute from './ProtectedRoute'

const AdminAttendancePage = lazy(() => import('../pages/admin/AdminAttendancePage'))
const AdminDashboardPage = lazy(() => import('../pages/admin/AdminDashboardPage'))
const AdminEmployeesPage = lazy(() => import('../pages/admin/AdminEmployeesPage'))
const AdminLeaveApprovalsPage = lazy(() => import('../pages/admin/AdminLeaveApprovalsPage'))
const AdminPayrollPage = lazy(() => import('../pages/admin/AdminPayrollPage'))
const LoginPage = lazy(() => import('../pages/auth/LoginPage'))
const SignupPage = lazy(() => import('../pages/auth/SignupPage'))
const EmployeeAttendancePage = lazy(() => import('../pages/employee/EmployeeAttendancePage'))
const EmployeeDashboardPage = lazy(() => import('../pages/employee/EmployeeDashboardPage'))
const EmployeeLeavePage = lazy(() => import('../pages/employee/EmployeeLeavePage'))
const EmployeePayrollPage = lazy(() => import('../pages/employee/EmployeePayrollPage'))
const EmployeeProfilePage = lazy(() => import('../pages/employee/EmployeeProfilePage'))

function RouteFallback() {
  return (
    <div className="route-fallback">
      <div className="route-fallback-card">
        <p className="eyebrow">Loading workspace</p>
        <h2>Preparing the dashboard experience</h2>
        <p className="muted">Sections, charts and approvals are loading with a lightweight split bundle.</p>
      </div>
    </div>
  )
}

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
    <Suspense fallback={<RouteFallback />}>
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
    </Suspense>
  )
}

export default AppRoutes
