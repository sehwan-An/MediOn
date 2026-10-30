import { useState } from 'react'
import { Link, Navigate, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { bookAppointment } from '../../api/appointments'
import { getDoctor } from '../../api/doctors'
import { getQuestion } from '../../api/questions'
import { departmentName } from '../../constants/departments'
import useAuth from '../../context/useAuth'
import { ageGroup, formatSlot, genderLabel } from '../../utils/format'
import TopBar from '../../components/layout/TopBar'
import Button from '../../components/ui/Button'
import { buttonClass } from '../../components/ui/buttonStyles'
import Card from '../../components/ui/Card'
import Icon from '../../components/ui/Icon'
import TextField from '../../components/ui/TextField'
import { ErrorState, LoadingState } from '../../components/ui/States'

const MEMO_MAX = 500
const THIS_YEAR = new Date().getFullYear()

// 예약하기 (I-2). 의사 상세에서 고른 시간이 ?slot= 으로 넘어온다
// 진료받는 사람은 지금은 본인만 (가족 예약 I-5 는 이후)
export default function BookPage() {
  const { id } = useParams()
  const [params] = useSearchParams()
  const slot = params.get('slot')
  const questionId = params.get('question')
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user, refreshMe } = useAuth()
  const [typedMemo, setTypedMemo] = useState(null) // null = 아직 안 고침 → 질문 내용을 기본값으로
  const [birthYear, setBirthYear] = useState('')
  const [birthError, setBirthError] = useState('')

  const doctor = useQuery({ queryKey: ['doctor', id], queryFn: () => getDoctor(id) })
  // 질문 → 예약 연결 (C-7): 질문 제목·내용을 증상 메모로 미리 채운다
  const question = useQuery({ queryKey: ['question', questionId], queryFn: () => getQuestion(questionId), enabled: Boolean(questionId) })
  const questionMemo = question.data ? `[질문] ${question.data.title}\n${question.data.body}`.slice(0, MEMO_MAX) : ''
  const memo = typedMemo ?? questionMemo
  const setMemo = setTypedMemo
  const mutation = useMutation({
    mutationFn: bookAppointment,
    onSuccess: (appointment) => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] })
      queryClient.invalidateQueries({ queryKey: ['slots', Number(id)] })
      if (!user.birth_year) refreshMe()
      navigate(`/appointments/${appointment.id}`, { replace: true, state: { justBooked: true } })
    },
    onError: (error) => {
      // 그사이 다른 사람이 같은 시간을 예약했으면 다시 고를 수 있게 슬롯을 새로 불러온다
      if (error.code === 'SLOT_TAKEN' || error.code === 'INVALID_SLOT') {
        queryClient.invalidateQueries({ queryKey: ['slots', Number(id)] })
      }
    },
  })

  if (!slot) return <Navigate to={`/doctors/${id}`} replace />
  if (doctor.isPending) return <><TopBar title="예약하기" /><LoadingState /></>
  if (doctor.isError) return <><TopBar title="예약하기" /><ErrorState message={doctor.error.message} /></>

  const d = doctor.data
  const needsBirthYear = !user.birth_year
  const slotGone = ['SLOT_TAKEN', 'INVALID_SLOT'].includes(mutation.error?.code)

  const handleSubmit = (event) => {
    event.preventDefault()
    const payload = { doctor_id: d.id, start_at: slot, symptom_note: memo || null }
    if (needsBirthYear) {
      const year = Number(birthYear)
      if (!Number.isInteger(year) || year < 1900 || year > THIS_YEAR) {
        setBirthError('출생연도를 확인해주세요')
        return
      }
      setBirthError('')
      payload.birth_year = year
    }
    mutation.mutate(payload)
  }

  const subjectMeta = [ageGroup(user.birth_year || Number(birthYear) || null), genderLabel(user.gender)].filter(Boolean).join(' · ')

  return (
    <form onSubmit={handleSubmit} noValidate className="flex flex-1 flex-col">
      <TopBar title="예약하기" />
      <div className="flex flex-col gap-5 p-5">
        <Card>
          <div className="flex items-center gap-3">
            <span className="flex size-11 shrink-0 items-center justify-center rounded-full bg-doctor-soft text-[17px] font-bold text-doctor">
              {d.name.slice(0, 1)}
            </span>
            <div className="flex flex-col">
              <p className="text-base font-bold">{d.name} 의사 · {departmentName(d.department_code)}</p>
              <p className="text-[13px] text-ink-muted">{d.hospital_name}</p>
            </div>
          </div>
          <dl className="flex flex-col gap-1 text-sm">
            <div className="flex justify-between py-1">
              <dt className="text-ink-muted">진료일</dt>
              <dd className="font-medium">{formatSlot(slot)}</dd>
            </div>
            <div className="flex justify-between py-1">
              <dt className="text-ink-muted">진료 방식</dt>
              <dd className="font-medium">비대면 진료</dd>
            </div>
          </dl>
        </Card>

        <section className="flex flex-col gap-2">
          <h2 className="text-[17px] font-bold">진료받는 사람</h2>
          <div className="flex items-center gap-3 rounded-[14px] border-2 border-primary bg-primary-soft px-4 py-3.5">
            <span className="flex flex-1 flex-col">
              <span className="text-[15px] font-bold">본인 · {user.nickname}</span>
              {subjectMeta && <span className="text-[13px] text-ink-muted">{subjectMeta}</span>}
            </span>
            <span className="flex size-[22px] items-center justify-center rounded-full bg-primary text-white">
              <Icon name="checkMark" size={14} />
            </span>
          </div>
          <p className="text-xs text-ink-muted">가족 대신 예약하는 기능은 준비 중이에요</p>
        </section>

        {needsBirthYear && (
          <TextField
            label="출생연도"
            inputMode="numeric"
            placeholder="예: 1995"
            maxLength={4}
            value={birthYear}
            onChange={(e) => setBirthYear(e.target.value.replace(/\D/g, ''))}
            hint="진료비는 진료받는 사람의 나이로 정해져요. 한 번 입력하면 저장돼요"
            error={birthError}
          />
        )}

        <section className="flex flex-col gap-2">
          <label htmlFor="symptom-memo" className="flex items-center gap-1 text-[17px] font-bold">
            증상 메모 <span className="text-[13px] font-normal text-ink-muted">선택</span>
          </label>
          <div className="flex flex-col gap-2 rounded-[14px] border border-line bg-white px-4 py-3.5 focus-within:border-primary">
            <textarea
              id="symptom-memo"
              rows={4}
              maxLength={MEMO_MAX}
              value={memo}
              onChange={(e) => setMemo(e.target.value)}
              placeholder="언제부터, 어디가, 어떻게 불편한지 적어주세요"
              className="resize-none text-[15px] outline-none placeholder:text-ink-muted"
            />
            <span className="self-end text-xs text-ink-muted">
              {memo.length} / {MEMO_MAX}
            </span>
          </div>
        </section>

        <p className="flex gap-2 rounded-xl bg-primary-soft px-3.5 py-3 text-[13px] font-medium text-primary">
          <Icon name="info" size={18} className="shrink-0" />
          진료비는 진료가 끝난 뒤 결제해요. 진료 시작 전까지 예약을 취소할 수 있어요.
        </p>
      </div>

      <div className="sticky bottom-0 mt-auto flex flex-col gap-2 border-t border-line bg-white px-5 pt-3 pb-6">
        {mutation.isError && (
          <p role="alert" className="flex items-center gap-1.5 text-[13px] text-wait">
            <Icon name="alert" size={16} />
            {mutation.error.message}
          </p>
        )}
        {slotGone ? (
          <Link to={`/doctors/${d.id}`} replace className={buttonClass('primary', 'w-full')}>
            다른 시간 선택하기
          </Link>
        ) : (
          <Button type="submit" className="w-full" disabled={mutation.isPending}>
            {mutation.isPending ? '예약하는 중…' : '예약 확정하기'}
          </Button>
        )}
      </div>
    </form>
  )
}
