import { useState } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { completeConsultation, getDoctorAppointment, searchDrugs } from '../../api/consultation'
import { VISIT_TYPE } from '../../constants/appointments'
import TopBar from '../../components/layout/TopBar'
import PrescriptionItems from '../../components/appointment/PrescriptionItems'
import BottomSheet from '../../components/ui/BottomSheet'
import Button from '../../components/ui/Button'
import Icon from '../../components/ui/Icon'
import Pill from '../../components/ui/Pill'
import TextField from '../../components/ui/TextField'
import { ErrorState, LoadingState } from '../../components/ui/States'

const SUMMARY_MAX = 1000
const FIRST_VISIT_MAX_DAYS = 7 // 백엔드 consultation_service 와 같은 값 (L-2)

// 진료 완료 · 처방전 작성 (J-4, L-1, L-2). 완료하면 요약·처방전이 한 번에 저장된다
export default function DoctorCompletePage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [summary, setSummary] = useState('')
  const [withRx, setWithRx] = useState(true)
  const [items, setItems] = useState([]) // { drug, dose, times_per_day, days, instruction }
  const [note, setNote] = useState('식후 30분에 복용하세요')
  const [sheetOpen, setSheetOpen] = useState(false)
  const [formError, setFormError] = useState('')

  const detail = useQuery({ queryKey: ['doctor-appointment', id], queryFn: () => getDoctorAppointment(id) })
  const complete = useMutation({
    mutationFn: (payload) => completeConsultation(id, payload),
    onSuccess: (data) => {
      queryClient.setQueryData(['doctor-appointment', id], data)
      queryClient.invalidateQueries({ queryKey: ['schedule'] })
      navigate(`/doctor/appointments/${id}`, { replace: true })
    },
    onError: (error) => setFormError(error.message),
  })

  if (detail.isPending) return <><TopBar title="진료 완료" /><LoadingState /></>
  if (detail.isError) return <><TopBar title="진료 완료" /><ErrorState message={detail.error.message} /></>
  const a = detail.data
  if (a.status !== 'in_progress') return <Navigate to={`/doctor/appointments/${id}`} replace />
  const maxDays = a.visit_type === 'first' ? FIRST_VISIT_MAX_DAYS : 90

  const handleSubmit = (event) => {
    event.preventDefault()
    if (!summary.trim()) return setFormError('진료 요약을 입력해주세요')
    if (withRx && items.length === 0) return setFormError('처방할 약을 추가하거나 "처방 없음"을 선택해주세요')
    setFormError('')
    complete.mutate({
      summary,
      prescription: withRx
        ? {
            note: note || null,
            items: items.map(({ drug, ...rest }) => ({ ...rest, drug_id: drug.id, instruction: rest.instruction || null })),
          }
        : null,
    })
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="flex flex-1 flex-col">
      <TopBar title="진료 완료" />
      <div className="flex flex-col gap-5 p-5">
        <div className="flex items-center gap-2.5 rounded-2xl bg-white px-4 py-3.5">
          <span className="text-[15px] font-bold">{a.subject_name}</span>
          <Pill tone={a.visit_type === 'first' ? 'wait' : 'muted'}>{VISIT_TYPE[a.visit_type]}</Pill>
        </div>

        <section className="flex flex-col gap-2">
          <label htmlFor="summary" className="flex items-center gap-1 text-base font-bold">
            진료 요약 <span className="text-[13px] font-normal text-ink-muted">환자에게 보여요</span>
          </label>
          <div className="flex flex-col gap-2 rounded-[14px] border border-line bg-white px-4 py-3.5 focus-within:border-doctor">
            <textarea
              id="summary"
              rows={5}
              maxLength={SUMMARY_MAX}
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              placeholder="확인한 증상과 생활 안내, 대면 진료가 필요한 경우를 적어주세요"
              className="resize-none text-[15px] outline-none placeholder:text-ink-muted"
            />
            <span className="self-end text-xs text-ink-muted">
              {summary.length} / {SUMMARY_MAX}
            </span>
          </div>
        </section>

        <section className="flex flex-col gap-3">
          <h2 className="text-base font-bold">처방</h2>
          <div role="radiogroup" aria-label="처방 여부" className="grid grid-cols-2 gap-1 rounded-xl bg-surface p-1">
            {[
              [true, '처방 있음'],
              [false, '처방 없음'],
            ].map(([value, label]) => (
              <button
                key={label}
                type="button"
                role="radio"
                aria-checked={withRx === value}
                onClick={() => setWithRx(value)}
                className={`h-10 rounded-[10px] text-sm ${withRx === value ? 'bg-white font-bold text-doctor' : 'font-medium text-ink-muted'}`}
              >
                {label}
              </button>
            ))}
          </div>

          {withRx && (
            <>
              {items.length > 0 && (
                <div className="rounded-[18px] bg-white px-[18px] py-1">
                  <PrescriptionItems prescription={{ items }} onRemove={(i) => setItems((list) => list.filter((_, j) => j !== i))} />
                </div>
              )}
              <button
                type="button"
                onClick={() => setSheetOpen(true)}
                className="flex h-13 items-center justify-center gap-1.5 rounded-[14px] border border-dashed border-doctor text-[15px] font-bold text-doctor"
              >
                <Icon name="search" size={18} />약 검색해서 추가
              </button>
              {a.visit_type === 'first' && (
                <p className="flex gap-2 rounded-xl bg-wait-soft px-3.5 py-3 text-[13px] font-medium text-wait">
                  <Icon name="info" size={18} className="shrink-0" />
                  초진이라 투약 일수는 최대 {FIRST_VISIT_MAX_DAYS}일까지 입력할 수 있어요
                </p>
              )}
              <TextField label="복용 안내" maxLength={300} value={note} onChange={(e) => setNote(e.target.value)} />
            </>
          )}
        </section>

        <p className="flex gap-2 rounded-xl bg-primary-soft px-3.5 py-3 text-[13px] font-medium text-primary">
          <Icon name="info" size={18} className="shrink-0" />
          완료하면 진료 요약과 처방전이 한 번에 저장되고, 환자 화면이 "진료 완료"로 바뀌어요
        </p>
      </div>

      <div className="sticky bottom-0 mt-auto flex flex-col gap-2 border-t border-line bg-white px-5 pt-3 pb-6">
        {formError && (
          <p role="alert" className="flex items-center gap-1.5 text-[13px] text-wait">
            <Icon name="alert" size={16} />
            {formError}
          </p>
        )}
        <Button type="submit" variant="doctor" className="w-full" disabled={complete.isPending}>
          {complete.isPending ? '저장하는 중…' : withRx ? '진료 완료하고 처방전 발급' : '진료 완료하기'}
        </Button>
      </div>

      <DrugSheet
        open={sheetOpen}
        maxDays={maxDays}
        onClose={() => setSheetOpen(false)}
        onAdd={(item) => {
          setItems((list) => [...list, item])
          setSheetOpen(false)
        }}
      />
    </form>
  )
}

// 약 검색 바텀시트 (L-1). 시드 데이터의 데모 약에서 검색한다
function DrugSheet({ open, maxDays, onClose, onAdd }) {
  const [q, setQ] = useState('')
  const [drug, setDrug] = useState(null)
  const [dose, setDose] = useState('1정')
  const [times, setTimes] = useState(3)
  const [days, setDays] = useState(3)
  const [instruction, setInstruction] = useState('식후 30분')
  const drugs = useQuery({ queryKey: ['drugs', q], queryFn: () => searchDrugs(q), enabled: open, placeholderData: (prev) => prev })

  const clamp = (value, max) => Math.min(Math.max(Number(value) || 1, 1), max)
  const add = () => {
    onAdd({ drug, dose: dose.trim() || '1정', times_per_day: times, days: clamp(days, maxDays), instruction: instruction.trim() })
    setDrug(null)
    setQ('')
  }

  return (
    <BottomSheet open={open} onClose={onClose} titleId="drug-sheet-title">
      <h2 id="drug-sheet-title" className="pt-2 text-xl font-bold">약 검색</h2>
      <TextField
        aria-label="약 이름"
        placeholder="약 이름으로 검색 (예: 해열)"
        value={q}
        onChange={(e) => {
          setQ(e.target.value)
          setDrug(null)
        }}
      />
      {drug ? (
        <div className="flex flex-col gap-3">
          <p className="flex items-center justify-between rounded-xl bg-doctor-soft px-4 py-3 text-[15px] font-bold text-doctor">
            {drug.name}
            <button type="button" onClick={() => setDrug(null)} className="text-[13px] font-medium">다시 고르기</button>
          </p>
          <div className="grid grid-cols-3 gap-2">
            <TextField label="1회 투약량" value={dose} maxLength={20} onChange={(e) => setDose(e.target.value)} />
            <TextField label="1일 횟수" type="number" min={1} max={6} value={times} onChange={(e) => setTimes(clamp(e.target.value, 6))} />
            <TextField label="투약 일수" type="number" min={1} max={maxDays} value={days} onChange={(e) => setDays(e.target.value)} hint={`최대 ${maxDays}일`} />
          </div>
          <TextField label="복용 방법" value={instruction} maxLength={100} onChange={(e) => setInstruction(e.target.value)} />
          <Button variant="doctor" className="w-full" onClick={add}>처방에 추가하기</Button>
        </div>
      ) : (
        <ul className="flex max-h-72 flex-col overflow-y-auto" aria-label="검색 결과">
          {drugs.isError && <li className="py-3 text-sm text-wait">{drugs.error.message}</li>}
          {drugs.data?.length === 0 && <li className="py-3 text-sm text-ink-muted">검색 결과가 없어요</li>}
          {drugs.data?.map((d) => (
            <li key={d.id}>
              <button type="button" onClick={() => setDrug(d)} className="flex min-h-13 w-full items-center gap-3 text-left">
                <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-surface text-ink-muted">
                  <Icon name="pill" size={18} />
                </span>
                <span className="flex flex-1 flex-col">
                  <span className="text-[15px] font-bold">{d.name}</span>
                  <span className="text-xs text-ink-muted">{d.maker} · {d.form}</span>
                </span>
                <span className="text-[13px] font-bold text-doctor">선택</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      <p className="text-xs text-ink-muted">데모용 가상 약 목록이에요</p>
    </BottomSheet>
  )
}
