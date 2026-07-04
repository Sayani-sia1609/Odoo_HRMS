import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function getDashboardPath(role) {
  if (role === 'admin') {
    return '/admin/dashboard'
  }

  if (role === 'employee') {
    return '/employee/dashboard'
  }

  return '/login'
}

function ProtectedRoute({ allowedRole }) {
  const { isAuthenticated, role } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (allowedRole && role !== allowedRole) {
    return <Navigate to={getDashboardPath(role)} replace />
  }

  return <Outlet />
}

export default ProtectedRoute
