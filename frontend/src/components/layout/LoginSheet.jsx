import { useNavigate } from 'react-router-dom'
import useLoginPrompt from '../../context/useLoginPrompt'
import BottomSheet from '../ui/BottomSheet'
import Button from '../ui/Button'
import Icon from '../ui/Icon'

// 로그인 안내 바텀시트 (A-6). AppLayout 이 프레임 안에 한 번 그린다
export default function LoginSheet() {
  const { prompt, close } = useLoginPrompt()
  const navigate = useNavigate()

  const goTo = (path) => {
    close()
    navigate(path, { state: { from: prompt.from } })
  }

  return (
    <BottomSheet open={Boolean(prompt)} onClose={close} titleId="login-sheet-title">
      <div className="flex flex-col items-center gap-1.5 pt-4 pb-2 text-center">
        <span className="flex size-13 items-center justify-center rounded-full bg-primary-soft text-primary">
          <Icon name="calendar" size={26} />
        </span>
        <h2 id="login-sheet-title" className="text-xl font-bold">
          로그인이 필요해요
        </h2>
        <p className="text-sm whitespace-pre-line text-ink-muted">{prompt?.message}</p>
      </div>
      <Button className="w-full" onClick={() => goTo('/login')}>
        로그인
      </Button>
      <Button variant="secondary" className="w-full" onClick={() => goTo('/signup')}>
        회원가입
      </Button>
      <button type="button" onClick={close} className="min-h-11 px-4 text-sm font-medium text-ink-muted">
        계속 둘러보기
      </button>
    </BottomSheet>
  )
}
