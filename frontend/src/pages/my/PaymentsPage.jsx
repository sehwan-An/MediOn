import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getMyPayments } from '../../api/payments'
import { won } from '../../constants/appointments'
import { formatDateTime } from '../../utils/format'
import TopBar from '../../components/layout/TopBar'
import Pill from '../../components/ui/Pill'
import { EmptyState, ErrorState, LoadingState } from '../../components/ui/States'

// 결제 내역 (K-5). 테스트 결제만 있다
export default function PaymentsPage() {
  const list = useQuery({ queryKey: ['my-payments'], queryFn: getMyPayments })
  return (
    <div className="flex flex-1 flex-col">
      <TopBar title="결제 내역" />
      <div className="flex flex-1 flex-col gap-3 p-5">
        {list.isPending && <LoadingState />}
        {list.isError && <ErrorState message={list.error.message} onRetry={list.refetch} />}
        {list.isSuccess && list.data.length === 0 && <EmptyState title="결제 내역이 없어요" />}
        {list.data?.map((p) => (
          <Link key={p.order_id} to={`/appointments/${p.appointment_id}`} className="flex flex-col gap-2 rounded-2xl bg-white px-[18px] py-4">
            <span className="flex items-center justify-between">
              <span className="text-[13px] font-medium text-ink-muted">{formatDateTime(p.approved_at)}</span>
              <Pill tone="done">결제 완료</Pill>
            </span>
            <span className="flex items-center justify-between gap-3">
              <span className="flex flex-col">
                <span className="text-[15px] font-bold">{p.order_name}</span>
                <span className="text-[13px] text-ink-muted">{p.method ?? '-'} (테스트)</span>
              </span>
              <span className="text-[17px] font-bold">{won(p.amount)}</span>
            </span>
          </Link>
        ))}
        {list.data?.length > 0 && <p className="text-center text-xs text-ink-muted">테스트 결제 내역이에요. 실제로 결제되지 않았어요.</p>}
      </div>
    </div>
  )
}
