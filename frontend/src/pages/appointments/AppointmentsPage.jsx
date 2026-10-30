import { Link, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getAppointments } from '../../api/appointments'
import { APPOINTMENT_STATUS, VISIT_TYPE } from '../../constants/appointments'
import { departmentName } from '../../constants/departments'
import { formatSlot } from '../../utils/format'
import PageHeader from '../../components/layout/PageHeader'
import { buttonClass } from '../../components/ui/buttonStyles'
import Pill from '../../components/ui/Pill'
import { EmptyState, ErrorState, LoadingState } from '../../components/ui/States'

const TABS = [
  { key: 'upcoming', label: '예정', empty: '예정된 진료가 없어요' },
  { key: 'past', label: '지난 진료', empty: '지난 진료가 없어요' },
  { key: 'cancelled', label: '취소', empty: '취소한 예약이 없어요' },
]

// 진료 내역 (I-7). 탭은 주소(?tab=)에 남겨서 상세에서 돌아와도 유지된다
export default function AppointmentsPage() {
  const [params, setParams] = useSearchParams()
  const tab = TABS.find((t) => t.key === params.get('tab')) ?? TABS[0]
  const list = useQuery({ queryKey: ['appointments', tab.key], queryFn: () => getAppointments(tab.key) })

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader title="진료 내역" />
      <div role="tablist" className="grid grid-cols-3 border-b border-line bg-white px-5">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={t.key === tab.key}
            onClick={() => setParams({ tab: t.key }, { replace: true })}
            className={`min-h-11 border-b-2 text-[15px] ${
              t.key === tab.key ? 'border-ink font-bold text-ink' : 'border-transparent font-medium text-ink-muted'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="flex flex-1 flex-col gap-3 p-5">
        {list.isPending && <LoadingState />}
        {list.isError && <ErrorState message={list.error.message} onRetry={list.refetch} />}
        {list.isSuccess && list.data.length === 0 && (
          <EmptyState
            title={tab.empty}
            action={tab.key === 'upcoming' && <Link to="/" className={buttonClass('primary')}>의사 찾아보기</Link>}
          />
        )}
        {list.isSuccess &&
          list.data.map((a) => {
            const status = APPOINTMENT_STATUS[a.status]
            return (
              <Link key={a.id} to={`/appointments/${a.id}`} className="flex flex-col gap-3 rounded-[18px] bg-white p-[18px]">
                <span className="flex items-center justify-between">
                  <Pill tone={status.tone}>{status.label}</Pill>
                  <span className="text-[13px] font-medium text-ink-muted">{formatSlot(a.start_at)}</span>
                </span>
                <span className="flex flex-col gap-0.5">
                  <span className="text-base font-bold">
                    {a.doctor.name} 의사 · {departmentName(a.doctor.department_code)}
                  </span>
                  <span className="text-[13px] text-ink-muted">
                    {a.doctor.hospital_name} · {VISIT_TYPE[a.visit_type]} · 진료받는 사람 {a.subject_name}
                  </span>
                </span>
              </Link>
            )
          })}
      </div>
    </div>
  )
}
