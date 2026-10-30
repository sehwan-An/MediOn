import { NavLink } from 'react-router-dom'
import useAuth from '../../context/useAuth'
import useLoginPrompt from '../../context/useLoginPrompt'
import Icon from '../ui/Icon'

// 하단 탭 (requirements 4. 하단 탭). 2차: 환자 "상담", 의사 "질문함"
// needsLogin: 게스트가 누르면 이동하지 않고 로그인 안내 바텀시트를 연다 (A-6)
const TABS = {
  patient: [
    { to: '/', label: '홈', icon: 'home', end: true },
    { to: '/appointments', label: '진료 내역', icon: 'clipboard', needsLogin: true },
    { to: '/qna', label: '상담', icon: 'chat' },
    { to: '/my', label: '마이', icon: 'user', end: true },
  ],
  doctor: [
    { to: '/doctor', label: '진료 일정', icon: 'calendar', end: true },
    { to: '/doctor/qna', label: '질문함', icon: 'inbox' },
    { to: '/doctor/my', label: '마이', icon: 'user' },
  ],
}

const itemClass = 'flex min-h-16 w-full flex-col items-center justify-center gap-1 text-xs'

export default function BottomNav({ role = 'patient' }) {
  const { user } = useAuth()
  const { requireLogin } = useLoginPrompt()
  const tabs = TABS[role]
  const activeColor = role === 'doctor' ? 'text-doctor' : 'text-primary'

  return (
    <nav
      aria-label="하단 메뉴"
      className="sticky bottom-0 z-20 w-full border-t border-line bg-white pb-[env(safe-area-inset-bottom)]"
    >
      <ul className={`grid ${{ 2: 'grid-cols-2', 3: 'grid-cols-3', 4: 'grid-cols-4' }[tabs.length]}`}>
        {tabs.map((tab) => (
          <li key={tab.to}>
            {tab.needsLogin && !user ? (
              <button
                type="button"
                className={`${itemClass} font-medium text-ink-muted`}
                onClick={() => requireLogin({ from: tab.to, message: `${tab.label}을 보려면 로그인해주세요.\n로그인하면 보던 화면으로 돌아와요.` })}
              >
                <Icon name={tab.icon} size={24} />
                {tab.label}
              </button>
            ) : (
              <NavLink
                to={tab.to}
                end={tab.end}
                className={({ isActive }) =>
                  `${itemClass} ${isActive ? `font-bold ${activeColor}` : 'font-medium text-ink-muted'}`
                }
              >
                <Icon name={tab.icon} size={24} />
                {tab.label}
              </NavLink>
            )}
          </li>
        ))}
      </ul>
    </nav>
  )
}
