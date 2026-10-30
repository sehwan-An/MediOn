import { useState } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getAppointment } from '../../api/appointments'
import { demoPay, getPayment } from '../../api/payments'
import { VISIT_TYPE, won } from '../../constants/appointments'
import useAuth from '../../context/useAuth'
import { ageGroup, formatSlot } from '../../utils/format'
import { loadScript } from '../../utils/loadScript'
import TopBar from '../../components/layout/TopBar'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Icon from '../../components/ui/Icon'
import { ErrorState, LoadingState } from '../../components/ui/States'

const TOSS_SDK = 'https://js.tosspayments.com/v2/standard'
const CLIENT_KEY = import.meta.env.VITE_TOSS_CLIENT_KEY
// 기본은 데모 결제(버튼을 누르면 바로 완료). VITE_PAYMENT_MODE=toss 이면 토스 테스트 결제창을 연다
const USE_TOSS = import.meta.env.VITE_PAYMENT_MODE === 'toss'

// 진료비 결제 (K-1, K-2). 금액은 서버가 정한 값만 쓴다. 어느 모드든 실제 돈은 나가지 않는다
export default function PaymentPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [opening, setOpening] = useState(false)
  const [error, setError] = useState('')
  const appointment = useQuery({ queryKey: ['appointment', id], queryFn: () => getAppointment(id) })
  const payment = useQuery({ queryKey: ['payment', id], queryFn: () => getPayment(id) })

  const demo = useMutation({
    mutationFn: () => demoPay(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointment', id] })
      queryClient.invalidateQueries({ queryKey: ['appointments'] })
      queryClient.invalidateQueries({ queryKey: ['my-payments'] })
      navigate(`/appointments/${id}`, { replace: true })
    },
    onError: (e) => setError(e.message),
  })

  if (appointment.isPending || payment.isPending) return <><TopBar title="결제" /><LoadingState /></>
  const failed = appointment.error ?? payment.error
  if (failed) return <><TopBar title="결제" /><ErrorState message={failed.message} /></>
  if (payment.data.status === 'paid') return <Navigate to={`/appointments/${id}`} replace />

  const a = appointment.data
  const p = payment.data

  const openToss = async () => {
    setError('')
    setOpening(true)
    try {
      await loadScript(TOSS_SDK)
      const origin = window.location.origin
      await window.TossPayments(CLIENT_KEY)
        .payment({ customerKey: p.customer_key })
        .requestPayment({
          method: 'CARD',
          amount: { currency: 'KRW', value: p.amount },
          orderId: p.order_id,
          orderName: p.order_name,
          customerName: user.nickname,
          successUrl: `${origin}/payments/success?appointment=${id}`,
          failUrl: `${origin}/payments/fail?appointment=${id}`,
        })
    } catch (e) {
      // 결제창을 닫으면 여기로 온다 (USER_CANCEL)
      setError(e?.code === 'USER_CANCEL' ? '결제를 취소했어요' : e?.message || '결제창을 열지 못했어요')
    } finally {
      setOpening(false)
    }
  }

  const pay = () => {
    setError('')
    if (USE_TOSS) openToss()
    else demo.mutate()
  }
  const busy = opening || demo.isPending
  const tossMissingKey = USE_TOSS && !CLIENT_KEY

  return (
    <div className="flex flex-1 flex-col">
      <TopBar title="결제" />
      <div className="flex flex-col gap-3 p-5">
        <Card className="gap-1.5">
          <h2 className="text-[15px] font-bold">결제 내용</h2>
          <Row label="주문" value={p.order_name} />
          <Row label="진료받는 사람" value={`${a.subject_name} · ${ageGroup(a.subject_birth_year)}`} />
          <Row label="진료일" value={formatSlot(a.start_at)} />
          <Row label="진료 구분" value={VISIT_TYPE[a.visit_type]} />
          <div className="mt-1 flex items-center justify-between border-t border-line pt-3">
            <span className="text-[15px] font-bold">결제할 금액</span>
            <span className="text-[22px] font-bold text-primary">{won(p.amount)}</span>
          </div>
        </Card>
        <p className="flex gap-2 rounded-xl bg-wait-soft px-3.5 py-3 text-[13px] font-medium text-wait">
          <Icon name="info" size={18} className="shrink-0" />
          {USE_TOSS
            ? '포트폴리오용 테스트 결제예요. 토스페이먼츠 테스트 결제창이 열리고, 실제 돈은 나가지 않아요.'
            : '포트폴리오용 데모 결제예요. 결제하기를 누르면 바로 결제 완료로 처리되고, 실제 돈은 나가지 않아요.'}
        </p>
        {tossMissingKey && (
          <p role="alert" className="rounded-xl bg-surface px-3.5 py-3 text-[13px] text-ink-muted">
            frontend/.env 에 VITE_TOSS_CLIENT_KEY(test_ck_…)를 넣고 프론트 서버를 다시 켜면 결제할 수 있어요.
          </p>
        )}
      </div>
      <div className="sticky bottom-0 mt-auto flex flex-col gap-2 border-t border-line bg-white px-5 pt-3 pb-6">
        {error && <p role="alert" className="text-[13px] text-wait">{error}</p>}
        <Button className="w-full" disabled={tossMissingKey || busy} onClick={pay}>
          {opening ? '결제창 여는 중…' : demo.isPending ? '결제하는 중…' : `${won(p.amount)} 결제하기`}
        </Button>
      </div>
    </div>
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
