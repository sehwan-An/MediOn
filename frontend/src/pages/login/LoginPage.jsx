import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { login as loginApi } from '../../api/auth'
import useAuth from '../../context/useAuth'
import { homePathFor } from '../../routes/homePath'
import { safeReturnPath } from '../../utils/format'
import TopBar from '../../components/layout/TopBar'
import Button from '../../components/ui/Button'
import Icon from '../../components/ui/Icon'
import TextField from '../../components/ui/TextField'
import { LoadingState } from '../../components/ui/States'

// 이메일 로그인 (A-8). 로그인 안내 바텀시트에서 왔으면 보던 화면으로 돌아간다 (A-6)
export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, loading, login, startAsGuest } = useAuth()
  const from = safeReturnPath(location.state?.from)

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [formError, setFormError] = useState('')

  const mutation = useMutation({
    mutationFn: loginApi,
    onSuccess: (data) => {
      login(data.access_token, data.user)
      // 의사·관리자는 각자의 첫 화면으로. 환자는 보던 화면(없으면 홈)으로
      const target = data.user.role === 'patient' && from ? from : homePathFor(data.user)
      navigate(target, { replace: true })
    },
    onError: (error) => setFormError(error.message),
  })

  if (loading) return <LoadingState />
  // 로그인 직후에는 onSuccess 가 이동시키므로, 이미 로그인한 채로 들어온 경우만 돌려보낸다
  if (user && !mutation.isSuccess) return <Navigate to={homePathFor(user)} replace />

  const handleSubmit = (event) => {
    event.preventDefault()
    if (!email.trim() || !password) {
      setFormError('이메일과 비밀번호를 입력해주세요')
      return
    }
    setFormError('')
    mutation.mutate({ email, password })
  }

  const handleGuest = () => {
    startAsGuest()
    navigate('/')
  }

  return (
    <div className="flex flex-1 flex-col bg-white">
      <TopBar title="로그인" />
      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-3 px-5 pt-6">
        <div className="mb-3 flex flex-col gap-1.5">
          <h2 className="text-2xl font-bold">다시 오신 걸 환영해요</h2>
          <p className="text-sm text-ink-muted">로그인하면 진료를 예약하고 진행 상황을 알림으로 받을 수 있어요</p>
        </div>
        <TextField
          type="email"
          name="email"
          autoComplete="email"
          placeholder="이메일"
          aria-label="이메일"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <TextField
          type={showPassword ? 'text' : 'password'}
          name="password"
          autoComplete="current-password"
          placeholder="비밀번호"
          aria-label="비밀번호"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          trailing={
            <button
              type="button"
              aria-label={showPassword ? '비밀번호 숨기기' : '비밀번호 보기'}
              onClick={() => setShowPassword((v) => !v)}
              className="flex size-11 items-center justify-center text-ink-muted"
            >
              <Icon name={showPassword ? 'eyeOff' : 'eye'} size={20} />
            </button>
          }
        />
        {formError && (
          <p role="alert" className="flex items-center gap-1.5 text-[13px] text-wait">
            <Icon name="alert" size={16} />
            {formError}
          </p>
        )}
        <Button type="submit" className="mt-2 w-full" disabled={mutation.isPending}>
          {mutation.isPending ? '로그인하는 중…' : '로그인'}
        </Button>
        <p className="flex items-center justify-center gap-1.5 text-sm text-ink-muted">
          아직 계정이 없나요?
          <Link to="/signup" state={{ from }} className="inline-flex min-h-11 items-center font-bold text-primary">
            회원가입
          </Link>
        </p>
      </form>

      <div className="mt-auto flex flex-col gap-2 px-5 pt-10 pb-8">
        <Link to="/signup/doctor" className="flex items-center gap-3 rounded-[18px] bg-doctor-soft px-[18px] py-4 text-doctor">
          <Icon name="steth" size={24} />
          <span className="flex flex-1 flex-col">
            <span className="text-[15px] font-bold">의사이신가요?</span>
            <span className="text-[13px]">면허 인증 후 비대면 진료를 할 수 있어요</span>
          </span>
          <Icon name="chevronRight" size={18} />
        </Link>
        <button type="button" onClick={handleGuest} className="min-h-11 text-sm font-medium text-ink-muted">
          로그인 없이 둘러보기
        </button>
      </div>
    </div>
  )
}
