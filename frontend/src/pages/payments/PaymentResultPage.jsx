import { Link, useSearchParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { confirmPayment, failPayment } from '../../api/payments'
import { won } from '../../constants/appointments'
import { formatDateTime } from '../../utils/format'
import { buttonClass } from '../../components/ui/buttonStyles'
import Card from '../../components/ui/Card'
import Icon from '../../components/ui/Icon'
import { LoadingState } from '../../components/ui/States'

// 토스 결제창에서 돌아오는 화면 (K-3, K-4). result: 'success' | 'fail'
// 승인 요청은 useQuery 로 한 번만 보낸다 (새로고침해도 서버가 같은 결과를 돌려준다)
export default function PaymentResultPage({ result }) {
  const [params] = useSearchParams()
  const queryClient = useQueryClient()
  const appointmentId = params.get('appointment')
  const orderId = params.get('orderId')

  const request = useQuery({
    queryKey: ['payment-result', result, orderId, params.get('paymentKey')],
    queryFn: async () => {
      const data =
        result === 'success'
          ? await confirmPayment({ payment_key: params.get('paymentKey'), order_id: orderId, amount: Number(params.get('amount')) })
          : await failPayment({ order_id: orderId, code: params.get('code') ?? 'UNKNOWN', message: params.get('message') ?? '결제를 완료하지 못했어요' })
      queryClient.invalidateQueries({ queryKey: ['appointment', appointmentId] })
      queryClient.invalidateQueries({ queryKey: ['payment', appointmentId] })
      queryClient.invalidateQueries({ queryKey: ['appointments'] })
      return data
    },
    retry: false,
    staleTime: Infinity,
    enabled: Boolean(orderId),
  })

  if (request.isPending && orderId) return <LoadingState message={result === 'success' ? '결제를 확인하고 있어요' : '잠시만요'} />

  const paid = result === 'success' && request.isSuccess
  const message = result === 'fail' ? params.get('message') : request.error?.message

  return (
    <main className="flex flex-1 flex-col">
      <div className="flex flex-col items-center gap-3 px-5 pt-14 pb-6 text-center">
        <span className={`flex size-18 items-center justify-center rounded-full ${paid ? 'bg-primary text-white' : 'bg-wait-soft text-wait'}`}>
          <Icon name={paid ? 'checkMark' : 'alert'} size={36} />
        </span>
        <h1 className="text-[22px] font-bold">{paid ? '결제가 완료됐어요' : '결제하지 못했어요'}</h1>
        <p className="text-sm text-ink-muted">
          {paid ? '이제 처방전을 보고 약을 받을 약국을 고를 수 있어요' : '진료비는 다시 결제할 수 있어요'}
        </p>
      </div>
      <div className="flex flex-col gap-3 px-5">
        {paid ? (
          <Card className="gap-1">
            <Row label="결제 금액" value={won(request.data.amount)} />
            <Row label="결제 수단" value={`${request.data.method ?? '-'} (테스트)`} />
            <Row label="결제 일시" value={formatDateTime(request.data.approved_at)} />
            <Row label="주문번호" value={request.data.order_id} />
            {request.data.receipt_url && (
              <a href={request.data.receipt_url} target="_blank" rel="noreferrer" className="mt-1 min-h-11 text-center text-[13px] font-medium text-ink-muted underline">
                영수증 보기
              </a>
            )}
          </Card>
        ) : (
          <Card className="gap-1">
            <h2 className="text-[15px] font-bold">실패 사유</h2>
            <p className="text-sm">{message || '결제를 완료하지 못했어요'}</p>
            {params.get('code') && <p className="text-xs text-ink-muted">{params.get('code')}</p>}
          </Card>
        )}
      </div>
      <div className="mt-auto flex flex-col gap-2 px-5 pt-6 pb-8">
        {paid ? (
          <Link to={`/appointments/${appointmentId}`} replace className={buttonClass('primary', 'w-full')}>
            처방전 보러 가기
          </Link>
        ) : (
          <Link to={`/appointments/${appointmentId}/pay`} replace className={buttonClass('primary', 'w-full')}>
            다시 결제하기
          </Link>
        )}
        <Link to={`/appointments/${appointmentId}`} replace className={buttonClass('secondary', 'w-full')}>
          예약 상세로
        </Link>
      </div>
    </main>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between gap-3 py-1 text-sm">
      <span className="text-ink-muted">{label}</span>
      <span className="text-right font-medium">{value}</span>
    </div>
  )
}
