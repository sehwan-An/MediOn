import { useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { cancelAppointment, getAppointment } from '../../api/appointments'
import { advancePharmacyOrder } from '../../api/payments'
import { APPOINTMENT_STATUS, CANCEL_REASONS, PHARMACY_FLOW, PHARMACY_STATUS, VISIT_TYPE, won } from '../../constants/appointments'
import { departmentName } from '../../constants/departments'
import { ageGroup, formatSlot } from '../../utils/format'
import TopBar from '../../components/layout/TopBar'
import VideoPlaceholder from '../../components/appointment/VideoPlaceholder'
import BottomSheet from '../../components/ui/BottomSheet'
import Button from '../../components/ui/Button'
import { buttonClass } from '../../components/ui/buttonStyles'
import Card from '../../components/ui/Card'
import Icon from '../../components/ui/Icon'
import Pill from '../../components/ui/Pill'
import { ErrorState, LoadingState } from '../../components/ui/States'

const STEPS = ['예약', '진료', '결제', '처방전', '약 수령']

// 진행 단계 (I-8): 예약 → 진료 → 결제 → 처방전 → 약 수령. 처방이 없으면 처방전·약 수령은 건너뜀(skipped)
function stepStates(a) {
  const paid = a.payment_status === 'paid'
  const order = a.pharmacy_order
  let current = 1
  if (a.status === 'completed') current = 2
  if (paid) current = a.has_prescription ? 3 : 5
  if (order) current = order.status === 'received' ? 5 : 4
  return STEPS.map((label, i) => {
    if (paid && !a.has_prescription && i >= 3) return { label, state: 'skipped' }
    return { label, state: i < current ? 'done' : i === current ? 'current' : 'todo' }
  })
}

const ORDER_HEADLINES = {
  sent: ['처방전을 보냈어요', '약국에서 확인하면 조제를 시작해요.'],
  preparing: ['약을 준비하고 있어요', '약이 준비되면 알려드려요.'],
  ready: ['약을 받으러 오세요', '약국에 방문해서 약을 받아가세요.'],
  shipping: ['약이 배송 중이에요', '곧 약을 받을 수 있어요.'],
  received: ['약을 받았어요', '진료가 모두 끝났어요. 몸조리 잘하세요.'],
}

function headline(a) {
  if (a.status === 'booked') return ['진료를 기다리고 있어요', `${formatSlot(a.start_at)}에 의사가 진료를 시작해요.`]
  if (a.status === 'in_progress') return ['진료 중이에요', `${a.doctor.name} 의사가 진료를 시작했어요. 진료가 끝나면 결제 안내가 와요.`]
  if (a.status === 'cancelled') return ['취소된 예약이에요', `사유: ${a.cancel_reason}`]
  if (a.pharmacy_order) return ORDER_HEADLINES[a.pharmacy_order.status]
  if (a.payment_status !== 'paid') return ['진료가 끝났어요', '진료비를 결제하면 처방전을 보고 약국을 고를 수 있어요.']
  if (a.has_prescription) return ['처방전이 준비됐어요', '처방전을 확인하고 약을 받을 약국을 골라주세요.']
  return ['진료가 모두 끝났어요', '처방 없이 진료를 마쳤어요.']
}

// 예약 상세 (I-8) · 예약 취소 (I-9). 예약 직후에는 완료 안내를 함께 보여준다
export default function AppointmentDetailPage() {
  const { id } = useParams()
  const location = useLocation()
  const queryClient = useQueryClient()
  const [sheetOpen, setSheetOpen] = useState(false)
  const [reason, setReason] = useState(CANCEL_REASONS[0])

  // 의사가 진료를 시작·완료하면 30초 안에 화면에 반영 (J-3). 끝난 예약은 다시 부르지 않는다
  const appointment = useQuery({
    queryKey: ['appointment', id],
    queryFn: () => getAppointment(id),
    refetchInterval: (query) => (['booked', 'in_progress'].includes(query.state.data?.status) ? 30000 : false),
  })
  const advance = useMutation({
    mutationFn: () => advancePharmacyOrder(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['appointment', id] }),
  })
  const cancel = useMutation({
    mutationFn: () => cancelAppointment(id, reason),
    onSuccess: (data) => {
      queryClient.setQueryData(['appointment', id], data)
      queryClient.invalidateQueries({ queryKey: ['appointments'] })
      queryClient.invalidateQueries({ queryKey: ['slots'] })
      setSheetOpen(false)
    },
  })

  if (appointment.isPending) return <><TopBar title="예약 상세" /><LoadingState /></>
  if (appointment.isError) return <><TopBar title="예약 상세" /><ErrorState message={appointment.error.message} /></>

  const a = appointment.data
  const status = APPOINTMENT_STATUS[a.status]
  const [title, sub] = headline(a)
  const paid = a.payment_status === 'paid'
  const order = a.pharmacy_order
  const justBooked = location.state?.justBooked && a.status === 'booked'
  const canCancel = a.status === 'booked' && new Date(a.start_at) > new Date()

  return (
    <div className="flex flex-1 flex-col">
      <TopBar title="예약 상세" />
      {justBooked && (
        <div role="status" className="flex flex-col items-center gap-2 bg-white px-5 pt-6 pb-4 text-center">
          <span className="flex size-14 items-center justify-center rounded-full bg-primary text-white">
            <Icon name="checkMark" size={28} />
          </span>
          <p className="text-xl font-bold">예약이 완료됐어요</p>
          <div className="mt-2 grid w-full grid-cols-2 gap-2">
            <Link to="/" replace className={buttonClass('soft')}>
              홈으로
            </Link>
            <Link to="/appointments" replace className={buttonClass('secondary')}>
              진료 내역
            </Link>
          </div>
        </div>
      )}
      <div className="flex flex-col gap-3 p-5">
        <Card className="gap-4">
          <div className="flex flex-col gap-1">
            <p className="flex items-center gap-2 text-xl font-bold">
              {title} <Pill tone={status.tone}>{status.label}</Pill>
            </p>
            <p className="text-sm text-ink-muted">{sub}</p>
          </div>
          {a.status !== 'cancelled' && <Progress steps={stepStates(a)} />}
        </Card>

        {a.status === 'in_progress' && <VideoPlaceholder description="지금은 의사가 진료 상태만 바꾸는 데모예요" />}

        {a.status === 'completed' && (
          <Card>
            <h2 className="text-[15px] font-bold">의사 진료 요약</h2>
            <p className="text-sm whitespace-pre-line">{a.doctor_summary}</p>
          </Card>
        )}
        {order && <PharmacyCard order={order} advancing={advance.isPending} error={advance.error?.message} onAdvance={() => advance.mutate()} />}

        {a.has_prescription &&
          (paid ? (
            <Link to={`/appointments/${a.id}/prescription`} className="flex items-center gap-3 rounded-[18px] bg-white px-[18px] py-4">
              <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-primary-soft text-primary">
                <Icon name="file" size={20} />
              </span>
              <span className="flex flex-1 flex-col">
                <span className="text-[15px] font-bold">처방전 보기</span>
                <span className="text-[13px] text-ink-muted">데모 처방전</span>
              </span>
              <Icon name="chevronRight" size={18} className="text-ink-muted" />
            </Link>
          ) : (
            <div className="flex items-center gap-3 rounded-[18px] bg-white px-[18px] py-4">
              <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-surface text-ink-muted">
                <Icon name="file" size={20} />
              </span>
              <span className="flex flex-col">
                <span className="text-[15px] font-bold">처방전이 발급됐어요</span>
                <span className="text-[13px] text-ink-muted">결제 후에 볼 수 있어요</span>
              </span>
            </div>
          ))}

        {paid && a.status === 'completed' &&
          (a.has_review ? (
            <p className="flex items-center gap-2 rounded-[18px] bg-white px-[18px] py-4 text-sm text-ink-muted">
              <Icon name="checkMark" size={18} className="text-done" />
              후기를 남겼어요. 고마워요!
            </p>
          ) : (
            <Link to={`/appointments/${a.id}/review`} className="flex items-center gap-3 rounded-[18px] bg-white px-[18px] py-4">
              <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-primary-soft text-primary">
                <Icon name="chat" size={20} />
              </span>
              <span className="flex flex-1 flex-col">
                <span className="text-[15px] font-bold">진료 후기 남기기</span>
                <span className="text-[13px] text-ink-muted">다른 환자가 의사를 고를 때 도움이 돼요</span>
              </span>
              <Icon name="chevronRight" size={18} className="text-ink-muted" />
            </Link>
          ))}

        <Card className="gap-1">
          <InfoRow label="의사" value={`${a.doctor.name} 의사 · ${departmentName(a.doctor.department_code)}`} />
          <InfoRow label="병원" value={a.doctor.hospital_name} />
          <InfoRow label="진료일" value={formatSlot(a.start_at)} />
          <InfoRow label="진료받는 사람" value={`${a.subject_name} · ${ageGroup(a.subject_birth_year)}`} />
          <InfoRow label="진료 구분" value={VISIT_TYPE[a.visit_type]} />
        </Card>

        {a.symptom_note && (
          <Card>
            <h2 className="text-[15px] font-bold">증상 메모</h2>
            <p className="text-sm whitespace-pre-line">{a.symptom_note}</p>
          </Card>
        )}
      </div>

      {(canCancel || (a.status === 'completed' && (!paid || (a.has_prescription && !order)))) && (
        <div className="sticky bottom-0 mt-auto border-t border-line bg-white px-5 pt-3 pb-6">
          {canCancel && (
            <Button variant="secondary" className="w-full" onClick={() => setSheetOpen(true)}>
              예약 취소하기
            </Button>
          )}
          {a.status === 'completed' && !paid && (
            <Link to={`/appointments/${a.id}/pay`} className={buttonClass('primary', 'w-full')}>
              {a.payment_amount ? `${won(a.payment_amount)} 결제하기` : '진료비 결제하기'}
            </Link>
          )}
          {paid && a.has_prescription && !order && (
            <Link to={`/appointments/${a.id}/pharmacy`} className={buttonClass('primary', 'w-full')}>
              약국 선택하기
            </Link>
          )}
        </div>
      )}

      <BottomSheet open={sheetOpen} onClose={() => setSheetOpen(false)} titleId="cancel-sheet-title">
        <div className="flex flex-col gap-1 pt-3 pb-1">
          <h2 id="cancel-sheet-title" className="text-xl font-bold">예약을 취소할까요?</h2>
          <p className="text-sm text-ink-muted">취소하면 이 시간은 다른 사람이 예약할 수 있어요</p>
        </div>
        <fieldset className="flex flex-col">
          <legend className="sr-only">취소 사유</legend>
          {CANCEL_REASONS.map((r) => (
            <label key={r} className="flex min-h-12 items-center gap-3 text-[15px]">
              <input type="radio" name="cancel-reason" className="size-5 accent-primary" checked={reason === r} onChange={() => setReason(r)} />
              {r}
            </label>
          ))}
        </fieldset>
        {cancel.isError && (
          <p role="alert" className="text-[13px] text-wait">{cancel.error.message}</p>
        )}
        <Button className="w-full" disabled={cancel.isPending} onClick={() => cancel.mutate()}>
          {cancel.isPending ? '취소하는 중…' : '예약 취소하기'}
        </Button>
        <Button variant="secondary" className="w-full" onClick={() => setSheetOpen(false)}>
          돌아가기
        </Button>
      </BottomSheet>
    </div>
  )
}

function InfoRow({ label, value }) {
  return (
    <div className="flex justify-between gap-3 py-1.5 text-sm">
      <span className="text-ink-muted">{label}</span>
      <span className="text-right font-medium">{value}</span>
    </div>
  )
}

// 진행 단계 (I-8, 피그마 Step)
function Progress({ steps }) {
  return (
    <ol className="flex items-start">
      {steps.map((s, i) => (
        <li key={s.label} className={`flex items-start ${i > 0 ? 'flex-1' : ''}`}>
          {i > 0 && <span aria-hidden="true" className={`mt-3 h-0.5 flex-1 ${['todo', 'skipped'].includes(s.state) ? 'bg-line' : 'bg-primary'}`} />}
          <span className="flex w-13 flex-col items-center gap-1.5">
            {s.state === 'done' && (
              <span className="flex size-6.5 items-center justify-center rounded-full bg-primary text-white">
                <Icon name="checkMark" size={14} />
              </span>
            )}
            {s.state === 'current' && (
              <span className="flex size-6.5 items-center justify-center rounded-full border-2 border-primary bg-primary-soft">
                <span className="size-2.5 rounded-full bg-primary" />
              </span>
            )}
            {s.state === 'todo' && <span className="size-6.5 rounded-full border-2 border-line bg-white" />}
            {s.state === 'skipped' && <span className="size-6.5 rounded-full border-2 border-dashed border-line bg-white" />}
            <span className={`text-[11px] ${s.state === 'current' ? 'font-bold text-primary' : s.state === 'done' ? 'font-medium' : 'text-ink-muted'}`}>
              {s.label}
              {s.state === 'current' && <span className="sr-only"> (현재 단계)</span>}
            </span>
          </span>
        </li>
      ))}
    </ol>
  )
}

// 약 수령 상태 (M-4) + 데모 상태 진행 버튼 (M-5)
function PharmacyCard({ order, advancing, error, onAdvance }) {
  const flow = PHARMACY_FLOW[order.receive_method]
  const index = flow.indexOf(order.status)
  return (
    <>
      <Card>
        <div className="flex items-center gap-3">
          <span className="flex size-11 shrink-0 items-center justify-center rounded-full bg-primary-soft text-primary">
            <Icon name="store" size={22} />
          </span>
          <span className="flex flex-1 flex-col">
            <span className="text-base font-bold">{order.pharmacy_name}</span>
            <span className="text-[13px] text-ink-muted">{order.pharmacy_address}</span>
          </span>
          {order.pharmacy_tel && (
            <a href={`tel:${order.pharmacy_tel}`} aria-label={`${order.pharmacy_name}에 전화하기`} className="flex size-11 items-center justify-center rounded-full bg-surface">
              <Icon name="phone" size={18} />
            </a>
          )}
        </div>
        <span>
          <Pill>{order.receive_method === 'pickup' ? '방문 수령' : '배송'}</Pill>
        </span>
        <ol className="flex flex-col">
          {flow.map((st, i) => {
            const state = i < index || order.status === 'received' ? 'done' : i === index ? 'current' : 'todo'
            return (
              <li key={st} className="flex min-h-10 items-center gap-3">
                {state === 'done' && (
                  <span className="flex size-6 items-center justify-center rounded-full bg-primary text-white"><Icon name="checkMark" size={14} /></span>
                )}
                {state === 'current' && (
                  <span className="flex size-6 items-center justify-center rounded-full border-2 border-primary bg-primary-soft"><span className="size-2.5 rounded-full bg-primary" /></span>
                )}
                {state === 'todo' && <span className="size-6 rounded-full border-2 border-line bg-white" />}
                <span className={`text-[15px] ${state === 'current' ? 'font-bold text-primary' : state === 'todo' ? 'text-ink-muted' : 'font-medium'}`}>
                  {PHARMACY_STATUS[st]}
                </span>
              </li>
            )
          })}
        </ol>
      </Card>
      {order.status !== 'received' && (
        <div className="flex flex-col gap-2.5 rounded-2xl bg-wait-soft p-4 text-wait">
          <p className="flex items-center gap-1.5 text-sm font-bold"><Icon name="info" size={18} />데모 기능</p>
          <p className="text-[13px]">약국 쪽 화면이 없어서 버튼으로 다음 단계로 넘겨요. 실제 약국에는 전송되지 않아요.</p>
          {error && <p role="alert" className="text-[13px]">{error}</p>}
          <button type="button" disabled={advancing} onClick={onAdvance} className="min-h-11 rounded-[10px] border border-wait bg-white text-sm font-bold disabled:opacity-50">
            데모: 다음 단계로
          </button>
        </div>
      )}
    </>
  )
}
