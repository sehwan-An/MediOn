import { useContext } from 'react'
import { LoginPromptContext } from './login-prompt-context'

// 게스트가 로그인이 필요한 기능을 누르면 로그인 안내 바텀시트를 연다 (A-6)
// 사용: const { requireLogin } = useLoginPrompt()
//       requireLogin({ from: '/appointments', message: '진료 내역을 보려면 로그인해주세요' })
export default function useLoginPrompt() {
  const value = useContext(LoginPromptContext)
  if (!value) throw new Error('useLoginPrompt 는 LoginPromptProvider 안에서만 쓸 수 있어요')
  return value
}
