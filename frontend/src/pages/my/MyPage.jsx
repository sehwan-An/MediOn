import { Link, useNavigate } from 'react-router-dom'
import useAuth from '../../context/useAuth'
import { ageGroup, genderLabel } from '../../utils/format'
import PageHeader from '../../components/layout/PageHeader'
import { buttonClass } from '../../components/ui/buttonStyles'
import Card from '../../components/ui/Card'
import Icon from '../../components/ui/Icon'
import MenuItem from '../../components/ui/MenuItem'

// 마이 (G-1, G-2, G-5, G-6). 로그인 상태면 프로필과 메뉴, 게스트면 로그인 안내
// 진료 요약(진료 횟수·결제 대기)은 예약 기능이 생기는 5단계 이후에 붙인다
export default function MyPage() {
  const { user } = useAuth()
  return (
    <div className="flex flex-1 flex-col">
      <PageHeader title="마이" />
      <div className="flex flex-col gap-3 p-5">{user ? <PatientMy user={user} /> : <GuestMy />}</div>
    </div>
  )
}

function PatientMy({ user }) {
  const navigate = useNavigate()
  const { logout } = useAuth()
  const meta = [ageGroup(user.birth_year), genderLabel(user.gender), user.email].filter(Boolean).join(' · ')

  const handleLogout = () => {
    logout()
    navigate('/welcome', { replace: true })
  }

  return (
    <>
      <Card>
        <div className="flex items-center gap-3.5">
          <span className="flex size-14 shrink-0 items-center justify-center rounded-full bg-primary-soft text-[22px] font-bold text-primary">
            {user.nickname.slice(0, 1)}
          </span>
          <div className="flex min-w-0 flex-col gap-0.5">
            <p className="text-lg font-bold">{user.nickname}</p>
            <p className="truncate text-[13px] text-ink-muted">{meta}</p>
          </div>
        </div>
      </Card>

      <nav aria-label="내 메뉴" className="overflow-hidden rounded-[18px] bg-white">
        <MenuItem icon="users" label="가족 관리" description="가족 대신 예약할 때 필요해요" to="/my/family" />
        <MenuItem icon="card" label="결제 내역" to="/my/payments" />
        <MenuItem icon="chat" label="내 질문" to="/my/questions" />
        <MenuItem icon="bell" label="알림" to="/notifications" />
      </nav>

      <div className="overflow-hidden rounded-[18px] bg-white">
        <MenuItem icon="logout" label="로그아웃" onClick={handleLogout} muted />
      </div>
    </>
  )
}

function GuestMy() {
  return (
    <>
      <Card className="gap-2.5">
        <div className="flex flex-col items-center gap-2.5 pt-2 pb-1 text-center">
          <span className="flex size-14 items-center justify-center rounded-full bg-surface text-ink-muted">
            <Icon name="user" size={28} />
          </span>
          <p className="text-[17px] font-bold">로그인하고 진료를 예약해보세요</p>
          <p className="text-[13px] text-ink-muted">의사 목록과 의사 정보는 로그인 없이 볼 수 있어요</p>
        </div>
        <Link to="/login" state={{ from: '/my' }} className={buttonClass('primary', 'w-full')}>
          로그인
        </Link>
        <Link to="/signup" state={{ from: '/my' }} className={buttonClass('secondary', 'w-full')}>
          회원가입
        </Link>
      </Card>

      <Link to="/signup/doctor" className="flex items-center gap-3 rounded-[18px] bg-doctor-soft px-[18px] py-4 text-doctor">
        <Icon name="steth" size={24} />
        <span className="flex flex-1 flex-col">
          <span className="text-[15px] font-bold">의사이신가요?</span>
          <span className="text-[13px]">면허 인증을 마치면 비대면 진료를 할 수 있어요</span>
        </span>
        <Icon name="chevronRight" size={18} />
      </Link>
    </>
  )
}
