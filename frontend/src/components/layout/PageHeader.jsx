import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getUnreadCount } from '../../api/notifications'
import useAuth from '../../context/useAuth'
import useLoginPrompt from '../../context/useLoginPrompt'
import Icon from '../ui/Icon'

// 탭 첫 화면의 상단 바: 큰 제목 + 알림 종 아이콘 (피그마 Page Header)
// 게스트가 종을 누르면 알림 페이지 대신 로그인 안내 바텀시트를 연다 (A-6)
// 로그인하면 안 읽은 알림 수를 30초마다 확인해서 종에 배지로 보여준다 (F-1, polling)
export default function PageHeader({ title, children = null }) {
  const { user } = useAuth()
  const { requireLogin } = useLoginPrompt()
  const unread = useQuery({
    queryKey: ['unread-count'],
    queryFn: getUnreadCount,
    enabled: Boolean(user),
    refetchInterval: 30 * 1000,
  })
  const count = user ? (unread.data?.count ?? 0) : 0
  const bellClass = 'relative flex size-11 items-center justify-center text-ink'

  return (
    <header className="sticky top-7 z-20 flex h-14 items-center justify-between bg-white pr-2 pl-5">
      {children ?? <h1 className="text-xl font-bold">{title}</h1>}
      {user ? (
        <Link to="/notifications" aria-label={count ? `알림, 안 읽은 알림 ${count}개` : '알림'} className={bellClass}>
          <Icon name="bell" />
          {count > 0 && (
            <span aria-hidden="true" className="absolute top-1.5 right-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-wait px-1 text-[10px] font-bold text-white">
              {count > 99 ? '99+' : count}
            </span>
          )}
        </Link>
      ) : (
        <button
          type="button"
          aria-label="알림"
          className={bellClass}
          onClick={() => requireLogin({ from: '/notifications', message: '알림을 보려면 로그인해주세요.\n로그인하면 보던 화면으로 돌아와요.' })}
        >
          <Icon name="bell" />
        </button>
      )}
    </header>
  )
}
