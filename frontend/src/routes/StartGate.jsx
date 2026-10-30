import { Navigate, Outlet } from 'react-router-dom'
import useAuth from '../context/useAuth'
import { LoadingState } from '../components/ui/States'
import { homePathFor } from './homePath'

// 처음 방문한 게스트는 시작 화면으로 (A-0). 의사·관리자는 각자의 첫 화면으로.
export default function StartGate() {
  const { user, loading, hasStarted } = useAuth()

  if (loading) return <LoadingState />
  if (user && user.role !== 'patient') return <Navigate to={homePathFor(user)} replace />
  if (!user && !hasStarted) return <Navigate to="/welcome" replace />
  return <Outlet />
}
