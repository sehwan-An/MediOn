import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getHealth } from '../../api/auth'
import useAuth from '../../context/useAuth'
import { homePathFor } from '../../routes/homePath'
import Button from '../../components/ui/Button'
import Icon from '../../components/ui/Icon'
import { LoadingState } from '../../components/ui/States'

const FEATURES = [
  { icon: 'calendar', title: '원하는 시간에 예약', description: '면허 인증을 마친 의사에게 30분 단위로 예약해요' },
  { icon: 'pill', title: '처방전과 약국 선택', description: '결제 후 처방전을 받고 가까운 약국을 골라요' },
  { icon: 'user', title: '로그인 없이 둘러보기', description: '의사 목록과 의사 정보는 로그인 없이 볼 수 있어요' },
]

// 시작 화면 (A-0, A-1)
export default function WelcomePage() {
  const navigate = useNavigate()
  const { user, loading, startAsGuest } = useAuth()
  // 무료 서버가 잠들어 있을 수 있어서 들어오자마자 깨운다
  const health = useQuery({ queryKey: ['health'], queryFn: getHealth, retry: 2, staleTime: Infinity })

  if (loading) return <LoadingState />
  if (user) return <Navigate to={homePathFor(user)} replace />

  const handleStart = () => {
    startAsGuest()
    navigate('/')
  }

  let statusText = '서버 준비 완료'
  if (health.isPending) statusText = '데모 서버를 깨우는 중이에요 · 최대 30초'
  if (health.isError) statusText = '서버에 연결하지 못했어요. 잠시 후 새로고침해주세요'

  return (
    <main className="flex flex-1 flex-col bg-doctor px-6 pt-14 pb-8 text-white">
      <section className="flex flex-col gap-4">
        <span className="text-4xl font-bold">MediON</span>
        <h1 className="text-[26px] leading-snug font-bold">
          병원 가기 힘들 땐
          <br />
          비대면 진료로 간편하게
        </h1>
        <p className="text-[15px] leading-relaxed text-doctor-soft">
          의사 찾기부터 예약, 진료, 처방전,
          <br />
          약 수령까지 한 번에
        </p>
      </section>

      <ul className="mt-auto flex flex-col gap-[18px] pt-10">
        {FEATURES.map((f) => (
          <li key={f.title} className="flex items-center gap-3.5">
            <span className="flex size-11 shrink-0 items-center justify-center rounded-full bg-white text-doctor">
              <Icon name={f.icon} size={22} />
            </span>
            <span className="flex flex-col gap-0.5">
              <span className="text-base font-bold">{f.title}</span>
              <span className="text-[13px] text-doctor-soft">{f.description}</span>
            </span>
          </li>
        ))}
      </ul>

      <div className="mt-10 flex flex-col items-center gap-1">
        <Button variant="secondary" className="mb-2 w-full" onClick={handleStart}>
          로그인 없이 시작하기
        </Button>
        <p className="flex items-center gap-1.5 text-sm text-doctor-soft">
          이미 계정이 있나요?
          <Link to="/login" className="inline-flex min-h-11 items-center font-bold text-white">
            로그인
          </Link>
        </p>
        <p className="flex items-center gap-1.5 text-sm text-doctor-soft">
          의사이신가요?
          <Link to="/signup/doctor" className="inline-flex min-h-11 items-center font-bold text-white">
            의사 회원가입
          </Link>
        </p>
        <p role="status" className="flex items-center gap-1.5 text-[13px] text-doctor-soft">
          <Icon name="loader" size={14} className={health.isPending ? 'animate-spin' : ''} />
          {statusText}
        </p>
      </div>
    </main>
  )
}
