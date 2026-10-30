import { useContext } from 'react'
import { AuthContext } from './auth-context'

export default function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth 는 AuthProvider 안에서만 쓸 수 있어요')
  return value
}
