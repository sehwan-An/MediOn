import { useCallback, useMemo, useState } from 'react'
import { LoginPromptContext } from './login-prompt-context'

const DEFAULT_MESSAGE = '로그인하면 보던 화면으로 돌아와요.'

// 로그인 안내 바텀시트의 열림 상태만 관리한다. 바텀시트 화면은 AppLayout 의 LoginSheet 가 그린다.
export default function LoginPromptProvider({ children }) {
  const [prompt, setPrompt] = useState(null) // { from, message } | null

  // from: 로그인한 뒤 돌아올 주소
  const requireLogin = useCallback(({ from, message = DEFAULT_MESSAGE } = {}) => {
    setPrompt({ from, message })
  }, [])

  const close = useCallback(() => setPrompt(null), [])

  const value = useMemo(() => ({ prompt, requireLogin, close }), [prompt, requireLogin, close])

  return <LoginPromptContext.Provider value={value}>{children}</LoginPromptContext.Provider>
}
