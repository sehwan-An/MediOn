import { useNavigate } from 'react-router-dom'
import useAuth from '../../context/useAuth'
import { departmentName } from '../../constants/departments'
import PageHeader from '../../components/layout/PageHeader'
import Card from '../../components/ui/Card'
import Icon from '../../components/ui/Icon'
import MenuItem from '../../components/ui/MenuItem'
import Pill from '../../components/ui/Pill'

const STATUS = {
  approved: { tone: 'done', label: '면허 인증 완료' },
  pending: { tone: 'wait', label: '인증 심사 중' },
  rejected: { tone: 'wait', label: '인증 반려' },
}

// 의사 마이 (G-1, G-2). 진료 통계(이번 달 진료 수·재진 희망률)는 진료·후기 기능이 생긴 뒤 붙인다
export default function DoctorMyPage() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const profile = user.doctor_profile
  const status = STATUS[profile?.verification_status] ?? STATUS.pending

  const handleLogout = () => {
    logout()
    navigate('/welcome', { replace: true })
  }

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader title="마이" />
      <div className="flex flex-col gap-3 p-5">
        <Card>
          <div className="flex items-center gap-3.5">
            <span className="flex size-14 shrink-0 items-center justify-center rounded-full bg-doctor-soft text-[22px] font-bold text-doctor">
              {(profile?.name ?? user.nickname).slice(0, 1)}
            </span>
            <div className="flex min-w-0 flex-col gap-1">
              <p className="flex items-center gap-1.5 text-lg font-bold">
                {profile?.name ?? user.nickname} 의사
                {profile?.verification_status === 'approved' && (
                  <Icon name="verified" size={18} className="text-doctor" />
                )}
              </p>
              {profile && (
                <p className="text-[13px] text-ink-muted">
                  {departmentName(profile.department_code)} · {profile.hospital_name}
                </p>
              )}
              <span>
                <Pill tone={status.tone}>{status.label}</Pill>
              </span>
            </div>
          </div>
        </Card>

        {profile?.bio && (
          <Card>
            <h2 className="text-[15px] font-bold">소개 문구</h2>
            <p className="text-sm">{profile.bio}</p>
          </Card>
        )}

        <div className="overflow-hidden rounded-[18px] bg-white">
          <MenuItem icon="calendar" label="진료 시간표" to="/doctor/schedule" />
          <MenuItem icon="chat" label="내 답변" to="/doctor/answers" />
          <MenuItem icon="logout" label="로그아웃" onClick={handleLogout} muted />
        </div>
      </div>
    </div>
  )
}
