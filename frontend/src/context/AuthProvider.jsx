import { useCallback, useEffect, useMemo, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getMe } from '../api/auth'
import { LOGOUT_EVENT } from '../api/client'
import { STARTED_KEY, storage, TOKEN_KEY } from '../utils/storage'
import { AuthContext } from './auth-context'

// 로그인 상태 관리. 토큰이 없으면 게스트(기본)
export default function AuthProvider({ children }) {
  const queryClient = useQueryClient()
  const [token, setToken] = useState(() => storage.get(TOKEN_KEY))
  const [hasStarted, setHasStarted] = useState(() => storage.get(STARTED_KEY) === '1')
  // 직접 로그아웃했는지. 보호된 화면에서 로그아웃하면 로그인 화면이 아니라 시작 화면으로 보내기 위해 쓴다 (G-2)
  const [loggedOut, setLoggedOut] = useState(false)

  const meQuery = useQuery({
    queryKey: ['me', token],
    queryFn: getMe,
    enabled: Boolean(token),
    retry: false,
    staleTime: 5 * 60 * 1000,
  })

  // 로그인·회원가입 응답에 사용자 정보가 같이 오므로 바로 캐시에 넣어서 /auth/me 를 다시 기다리지 않는다
  const login = useCallback(
    (newToken, me) => {
      storage.set(TOKEN_KEY, newToken)
      storage.set(STARTED_KEY, '1')
      if (me) queryClient.setQueryData(['me', newToken], me)
      setToken(newToken)
      setHasStarted(true)
      setLoggedOut(false)
    },
    [queryClient],
  )

  // byUser: 사용자가 로그아웃 버튼을 눌렀으면 true, 토큰 만료로 자동 로그아웃이면 false(다시 로그인 화면으로)
  const logout = useCallback((byUser = true) => {
    storage.remove(TOKEN_KEY)
    setToken(null)
    setLoggedOut(byUser)
    // 다른 사람이 같은 브라우저로 로그인해도 이전 사용자 데이터가 보이지 않게 캐시를 비운다
    queryClient.clear()
  }, [queryClient])

  const startAsGuest = useCallback(() => {
    storage.set(STARTED_KEY, '1')
    setHasStarted(true)
    setLoggedOut(false)
  }, [])

  // 토큰 만료 등으로 API 가 401 을 주면 client 인터셉터가 이 이벤트를 보낸다
  useEffect(() => {
    const onExpired = () => logout(false)
    window.addEventListener(LOGOUT_EVENT, onExpired)
    return () => window.removeEventListener(LOGOUT_EVENT, onExpired)
  }, [logout])

  const user = token ? (meQuery.data ?? null) : null
  const loading = Boolean(token) && meQuery.isPending

  const value = useMemo(
    () => ({ user, loading, isGuest: !user, hasStarted, loggedOut, login, logout, startAsGuest, refreshMe: meQuery.refetch }),
    [user, loading, hasStarted, loggedOut, login, logout, startAsGuest, meQuery.refetch],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
