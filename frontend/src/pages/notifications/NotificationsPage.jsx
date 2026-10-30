import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getNotifications, markAllNotificationsRead, markNotificationRead } from '../../api/notifications'
import useAuth from '../../context/useAuth'
import { formatDateTime } from '../../utils/format'
import TopBar from '../../components/layout/TopBar'
import Icon from '../../components/ui/Icon'
import { EmptyState, ErrorState, LoadingState } from '../../components/ui/States'

const ICONS = {
  appointment_booked: 'calendar',
  appointment_cancelled: 'calendar',
  consultation_started: 'steth',
  payment_requested: 'card',
  pharmacy_status: 'store',
  doctor_approved: 'verified',
  doctor_rejected: 'alert',
  answer_arrived: 'chat',
}

// 알림을 누르면 갈 곳: 환자는 예약 상세, 의사는 진료 상세, 인증 결과는 의사 첫 화면
function targetOf(n, role) {
  if (n.type === 'doctor_approved' || n.type === 'doctor_rejected') return '/doctor'
  if (n.question_id) return `/questions/${n.question_id}`
  if (!n.appointment_id) return null
  return role === 'doctor' ? `/doctor/appointments/${n.appointment_id}` : `/appointments/${n.appointment_id}`
}

// 알림 목록 (F-1, F-2). 누르면 읽음 처리하고 해당 화면으로, 모두 읽음
export default function NotificationsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user, refreshMe } = useAuth()
  const list = useQuery({ queryKey: ['notifications'], queryFn: () => getNotifications() })

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['notifications'] })
    queryClient.invalidateQueries({ queryKey: ['unread-count'] })
  }
  const readAll = useMutation({ mutationFn: markAllNotificationsRead, onSuccess: refresh })

  const open = async (n) => {
    if (!n.is_read) {
      await markNotificationRead(n.id).catch(() => {}) // 읽음 처리에 실패해도 이동은 한다
      refresh()
    }
    if (n.type === 'doctor_approved') await refreshMe() // 인증 상태를 새로 받아야 의사 화면이 열린다
    const to = targetOf(n, user.role)
    if (to) navigate(to)
  }

  const hasUnread = list.data?.some((n) => !n.is_read)

  return (
    <div className="flex flex-1 flex-col">
      <TopBar
        title="알림"
        right={hasUnread ? (
          <button type="button" onClick={() => readAll.mutate()} disabled={readAll.isPending}
            className="min-h-11 px-2 text-[13px] font-bold text-primary">
            모두 읽음
          </button>
        ) : null}
      />
      {list.isPending && <LoadingState />}
      {list.isError && <ErrorState message={list.error.message} onRetry={list.refetch} />}
      {list.isSuccess && list.data.length === 0 && (
        <EmptyState title="알림이 없어요" description="예약·진료·결제·약 수령 소식을 여기서 알려드려요" />
      )}
      {list.isSuccess && list.data.length > 0 && (
        <ul className="flex flex-col">
          {list.data.map((n) => (
            <li key={n.id}>
              <button
                type="button"
                onClick={() => open(n)}
                className={`flex w-full items-start gap-3 border-b border-line px-5 py-4 text-left ${n.is_read ? 'bg-white' : 'bg-primary-soft'}`}
              >
                <span className={`flex size-10 shrink-0 items-center justify-center rounded-full ${n.is_read ? 'bg-surface text-ink-muted' : 'bg-white text-primary'}`}>
                  <Icon name={ICONS[n.type] ?? 'bell'} size={20} />
                </span>
                <span className="flex flex-1 flex-col gap-1">
                  <span className={`text-[15px] ${n.is_read ? 'text-ink-muted' : 'font-bold text-ink'}`}>{n.message}</span>
                  <span className="text-xs text-ink-muted">{formatDateTime(n.created_at)}</span>
                </span>
                {!n.is_read && <span className="sr-only">안 읽음</span>}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
