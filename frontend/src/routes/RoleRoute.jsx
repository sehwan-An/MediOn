import { Navigate, Outlet, useLocation } from 'react-router-dom'
import useAuth from '../context/useAuth'
import { LoadingState } from '../components/ui/States'
import { homePathFor, isVerifiedDoctor } from './homePath'

// 역할별 라우트 보호 (A-3). 화면 편의용이며 실제 보안은 백엔드 권한 검사가 담당한다.
export default function RoleRoute({ roles, requireVerified = false }) {
  const { user, loading, loggedOut } = useAuth()
  const location = useLocation()

  if (loading) return <LoadingState />
  // 로그아웃 버튼을 눌러서 나간 경우는 시작 화면으로, 그 외(직접 주소 입력, 토큰 만료)는 로그인 후 돌아오게
  if (!user && loggedOut) return <Navigate to="/welcome" replace />
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  if (!roles.includes(user.role)) return <Navigate to={homePathFor(user)} replace />
  if (requireVerified && user.role === 'doctor' && !isVerifiedDoctor(user)) {
    return <Navigate to="/doctor/pending" replace />
  }
  return <Outlet />
}
