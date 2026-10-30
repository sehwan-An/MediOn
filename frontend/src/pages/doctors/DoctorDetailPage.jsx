import { useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getDoctor, getDoctorReviews } from '../../api/doctors'
import { REVIEW_TAGS } from '../../constants/appointments'
import { departmentName } from '../../constants/departments'
import useAuth from '../../context/useAuth'
import useLoginPrompt from '../../context/useLoginPrompt'
import { formatDateTime, formatSlot, todayHours } from '../../utils/format'
import TopBar from '../../components/layout/TopBar'
import ScheduleList from '../../components/doctor/ScheduleList'
import SlotPicker from '../../components/doctor/SlotPicker'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Icon from '../../components/ui/Icon'
import Pill from '../../components/ui/Pill'
import { EmptyState, ErrorState, LoadingState } from '../../components/ui/States'

const TABS = [
  { key: 'info', label: '의사 정보' },
  { key: 'fee', label: '진료비' },
  { key: 'review', label: '후기' },
]

// 의사 상세 (H-5, H-6). 시간을 고르고 예약하기를 누르면 예약 화면으로 (게스트는 로그인 안내, A-6)
export default function DoctorDetailPage() {
  const { id } = useParams()
  const [params] = useSearchParams()
  const questionId = params.get('question') // 질문 답변에서 왔으면 예약 때 질문 내용을 증상 메모로 (C-7)
  const navigate = useNavigate()
  const { user } = useAuth()
  const { requireLogin } = useLoginPrompt()
  const [tab, setTab] = useState('info')
  const [slot, setSlot] = useState(null)

  const doctor = useQuery({ queryKey: ['doctor', id], queryFn: () => getDoctor(id) })

  if (doctor.isPending) return <><TopBar title="의사 정보" /><LoadingState /></>
  if (doctor.isError) {
    return (
      <>
        <TopBar title="의사 정보" />
        <ErrorState message={doctor.error.message} onRetry={doctor.error.status === 404 ? undefined : doctor.refetch} />
      </>
    )
  }

  const d = doctor.data
  const handleBook = () => {
    if (!slot) {
      setTab('info')
      return
    }
    const bookPath = `/doctors/${d.id}/book?slot=${encodeURIComponent(slot)}${questionId ? `&question=${questionId}` : ''}`
    if (!user) {
      requireLogin({ from: bookPath, message: '예약하려면 로그인해주세요.\n로그인하면 고른 시간으로 예약을 이어가요.' })
      return
    }
    navigate(bookPath)
  }

  return (
    <div className="flex flex-1 flex-col">
      <TopBar title="의사 정보" />
      <section className="flex flex-col gap-4 bg-white px-5 pt-2">
        <div className="flex items-center gap-3.5">
          <span className="flex size-16 shrink-0 items-center justify-center rounded-full bg-doctor-soft text-2xl font-bold text-doctor">
            {d.name.slice(0, 1)}
          </span>
          <div className="flex min-w-0 flex-col gap-1">
            <p className="truncate text-[13px] text-ink-muted">{d.hospital_name}</p>
            <h2 className="flex items-center gap-1.5 text-xl font-bold">
              {d.name} 의사 <Icon name="verified" size={18} className="text-primary" />
            </h2>
            <span className="flex gap-1.5">
              <Pill>{departmentName(d.department_code)}</Pill>
              <Pill tone="done">면허 인증</Pill>
            </span>
          </div>
        </div>
        <dl className="grid grid-cols-3 rounded-2xl bg-surface py-3 text-center">
          <Stat label="재진 희망" value={d.review_count > 0 ? `${d.revisit_rate}%` : '-'} />
          <Stat label="후기" value={d.review_count} />
          <Stat label="오늘 진료" value={todayHours(d.schedules)} />
        </dl>
        <div role="tablist" className="grid grid-cols-3">
          {TABS.map((t) => (
            <button
              key={t.key}
              type="button"
              role="tab"
              aria-selected={tab === t.key}
              onClick={() => setTab(t.key)}
              className={`min-h-11 border-b-2 pt-1 text-[15px] ${
                tab === t.key ? 'border-ink font-bold text-ink' : 'border-transparent font-medium text-ink-muted'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </section>

      <div className="flex flex-1 flex-col gap-3 p-5">
        {tab === 'info' && (
          <>
            <Card>
              <h3 className="text-[17px] font-bold">예약 시간 선택</h3>
              <SlotPicker doctorId={d.id} schedules={d.schedules} value={slot} onChange={setSlot} />
            </Card>
            {d.bio && (
              <Card>
                <h3 className="text-[17px] font-bold">소개</h3>
                <p className="text-sm">{d.bio}</p>
              </Card>
            )}
            <Card className="gap-1">
              <h3 className="mb-1 text-[17px] font-bold">진료 시간표</h3>
              <ScheduleList schedules={d.schedules} />
            </Card>
          </>
        )}
        {tab === 'fee' && <FeeTab fees={d.fees} />}
        {tab === 'review' && <ReviewTab doctorId={d.id} />}
      </div>

      <div className="sticky bottom-0 border-t border-line bg-white px-5 pt-3 pb-6">
        <Button className="w-full" onClick={handleBook}>
          {slot ? `${formatSlot(slot)} 예약하기` : '예약 시간 선택하기'}
        </Button>
      </div>
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div className="flex flex-col-reverse gap-0.5">
      <dt className="text-xs text-ink-muted">{label}</dt>
      <dd className="text-[15px] font-bold">{value}</dd>
    </div>
  )
}

function FeeTab({ fees }) {
  const won = (n) => `${n.toLocaleString('ko-KR')}원`
  return (
    <>
      <p className="flex gap-2 rounded-xl bg-primary-soft px-3.5 py-3 text-[13px] font-medium text-primary">
        <Icon name="info" size={18} className="shrink-0" />
        진료비는 진료받는 사람의 나이와 초진·재진에 따라 정해져요. 표시된 금액은 데모 금액이에요.
      </p>
      <table className="overflow-hidden rounded-2xl bg-white text-sm">
        <thead className="bg-surface text-ink-muted">
          <tr>
            <th scope="col" className="px-4 py-3 text-left font-medium">진료받는 사람 나이</th>
            <th scope="col" className="px-4 py-3 text-right font-medium">초진</th>
            <th scope="col" className="px-4 py-3 text-right font-medium">재진</th>
          </tr>
        </thead>
        <tbody>
          {fees.map((f) => (
            <tr key={f.label} className="border-t border-line">
              <th scope="row" className="px-4 py-3 text-left font-normal">{f.label}</th>
              <td className="px-4 py-3 text-right font-bold">{won(f.first_visit)}</td>
              <td className="px-4 py-3 text-right font-bold">{won(f.return_visit)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <Card>
        <h3 className="text-[15px] font-bold">이렇게 결제돼요</h3>
        <ol className="list-decimal pl-5 text-sm leading-relaxed">
          <li>진료가 끝나면 결제 요청 알림이 와요</li>
          <li>앱에서 진료비를 결제해요 (테스트 결제)</li>
          <li>결제가 끝나면 처방전을 볼 수 있어요</li>
          <li>약값은 약을 받을 때 약국에서 따로 내요</li>
        </ol>
      </Card>
    </>
  )
}

// 후기 탭 (N-2): 재진 희망률, 태그별 인원, 후기 목록
function ReviewTab({ doctorId }) {
  const reviews = useQuery({ queryKey: ['doctor-reviews', String(doctorId)], queryFn: () => getDoctorReviews(doctorId) })
  if (reviews.isPending) return <LoadingState />
  if (reviews.isError) return <ErrorState message={reviews.error.message} onRetry={reviews.refetch} />
  const r = reviews.data
  if (r.review_count === 0) {
    return <EmptyState title="아직 후기가 없어요" description="진료를 받은 환자만 후기를 남길 수 있어요" />
  }
  const tagLabel = (value) => REVIEW_TAGS.find((t) => t.value === value)?.label ?? value
  return (
    <>
      <Card>
        <p className="text-sm text-ink-muted">
          후기 {r.review_count}개 중 <b className="text-xl text-primary">{r.revisit_rate}%</b>가 다시 진료받고 싶대요
        </p>
        <ul className="flex flex-col gap-2">
          {REVIEW_TAGS.map((t) => (
            <li key={t.value} className="flex items-center gap-3 text-sm">
              <span className="w-24 shrink-0">{t.label}</span>
              <span className="h-2 flex-1 overflow-hidden rounded-full bg-surface">
                <span className="block h-full rounded-full bg-primary" style={{ width: `${(100 * r.tag_counts[t.value]) / r.review_count}%` }} />
              </span>
              <span className="w-10 text-right font-bold">{r.tag_counts[t.value]}명</span>
            </li>
          ))}
        </ul>
      </Card>
      {r.items.map((item) => (
        <Card key={item.id} as="article" className="gap-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-bold">{item.author}</span>
            <span className="text-xs text-ink-muted">{formatDateTime(item.created_at).slice(0, 10)}</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            <Pill tone={item.wants_revisit ? 'done' : 'muted'}>{item.wants_revisit ? '재진 희망' : '재진 희망 안 함'}</Pill>
            {item.tags.map((t) => <Pill key={t}>{tagLabel(t)}</Pill>)}
          </div>
          {item.body && <p className="text-sm whitespace-pre-line">{item.body}</p>}
        </Card>
      ))}
    </>
  )
}
