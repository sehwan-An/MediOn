import { useEffect } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import useAuth from '../../context/useAuth'
import { formatDateTime } from '../../utils/format'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Icon from '../../components/ui/Icon'

// 인증 심사 중 (A-10). 승인 전 의사는 이 화면만 본다. 진료·처방 API 는 서버에서 403
// 서류를 다시 내는 기능(A-12)은 아직 없다. 30초마다 인증 상태를 다시 확인해서 승인되면 진료 일정으로 넘어간다
export default function DoctorPendingPage() {
  const navigate = useNavigate()
  const { user, logout, refreshMe } = useAuth()
  useEffect(() => {
    const timer = setInterval(() => refreshMe(), 30 * 1000)
    return () => clearInterval(timer)
  }, [refreshMe])
  const profile = user.doctor_profile
  const rejected = profile?.verification_status === 'rejected'

  if (profile?.verification_status === 'approved') return <Navigate to="/doctor" replace />

  const handleLogout = () => {
    logout()
    navigate('/welcome', { replace: true })
  }

  const steps = [
    { state: 'done', title: '서류 제출', description: formatDateTime(profile?.submitted_at) || '제출 완료' },
    rejected
      ? { state: 'current', title: '인증 반려', description: profile?.rejected_reason || '반려 사유를 확인해주세요' }
      : { state: 'current', title: '관리자 확인 중', description: '보통 1~2일 걸려요' },
    { state: 'todo', title: '진료 시작', description: '승인되면 진료 시간표가 열리고 예약을 받을 수 있어요' },
  ]

  return (
    <main className="flex flex-1 flex-col gap-5 px-5 pt-10 pb-8">
      <div className="flex flex-col items-center gap-3 text-center">
        <span className="flex size-16 items-center justify-center rounded-full bg-doctor-soft text-doctor">
          <Icon name={rejected ? 'alert' : 'clock'} size={32} />
        </span>
        <h1 className="text-[22px] font-bold">{rejected ? '인증이 반려됐어요' : '인증 심사 중이에요'}</h1>
        <p className="text-sm text-ink-muted">
          {rejected ? '반려 사유를 확인해주세요.' : '제출하신 서류를 확인하고 있어요.'}
          <br />
          승인되면 알림으로 알려드릴게요.
        </p>
      </div>

      <Card as="ol" className="gap-0">
        {steps.map((step, index) => (
          <li key={step.title} className="flex gap-3">
            <span className="flex flex-col items-center">
              <StepDot state={step.state} />
              {index < steps.length - 1 && <span aria-hidden="true" className="w-0.5 flex-1 bg-line" />}
            </span>
            <span className="flex flex-col gap-0.5 pb-4">
              <span className={`text-[15px] font-bold ${step.state === 'todo' ? 'text-ink-muted' : step.state === 'current' ? 'text-doctor' : 'text-ink'}`}>
                {step.title}
              </span>
              <span className="text-[13px] text-ink-muted">{step.description}</span>
            </span>
          </li>
        ))}
      </Card>

      <p className="text-center text-[13px] text-ink-muted">심사 중에는 진료·처방을 할 수 없어요</p>
      <Button variant="secondary" className="mt-auto w-full" onClick={handleLogout}>
        로그아웃
      </Button>
    </main>
  )
}

function StepDot({ state }) {
  if (state === 'done') {
    return (
      <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-doctor text-white">
        <Icon name="checkMark" size={14} />
      </span>
    )
  }
  if (state === 'current') {
    return (
      <span className="flex size-6 shrink-0 items-center justify-center rounded-full border-2 border-doctor bg-doctor-soft">
        <span className="size-2.5 rounded-full bg-doctor" />
      </span>
    )
  }
  return <span className="size-6 shrink-0 rounded-full border-2 border-line bg-white" />
}
