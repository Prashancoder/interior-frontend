import { Navigate, useLocation } from 'react-router-dom'
import { homePathForRole, useAuth } from '../auth'
import { LoadingState } from './LoadingState'

export default function ProtectedRoute({ roles, children }) {
  const { ready, isAuthenticated, user } = useAuth()
  const location = useLocation()

  if (!ready) return <LoadingState label="Checking session..." />
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }
  if (roles && !roles.includes(user.role)) {
    return <Navigate to={homePathForRole(user.role)} replace />
  }
  return children
}
