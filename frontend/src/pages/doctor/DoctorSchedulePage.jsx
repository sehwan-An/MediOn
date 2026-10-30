import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getSchedule } from '../../api/consultation'
import { APPOINTMENT_STATUS, VISIT_TYPE } from '../../constants/appointments'
import { ageGroup, formatSlot, genderLabel, upcomingDays } from '../../utils/format'
import PageHeader from '../../components/layout/PageHeader'
import Pill from '../../components/ui/Pill'
import { EmptyState, ErrorState, LoadingState } from '../../components/ui/States'

// 의사 진료 일정 (J-1). 날짜별 예약 목록, 시간순. 새 예약을 놓치지 않게 30초마다 다시 불러온다
export default function DoctorSchedulePage() {
  const [days] = useState(() => upcomingDays(7))
  const [dayKey, setDayKey] = useState(days[0].key)
  const schedule = useQuery({ queryKey: ['schedule', dayKey], queryFn: () => getSchedule(dayKey), refetchInterval: 30000 })

  const list = schedule.data ?? []
  const count = (status) => list.filter((a) => a.status === status).length

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader title="진료 일정" />
      <div className="flex flex-col gap-3.5 bg-white px-5 pt-1 pb-4">
        <div className="flex justify-between" role="radiogroup" aria-label="날짜">
          {days.map((d) => {
            const selected = d.key === dayKey
            return (
              <button
                key={d.key}
                type="button"
                role="radio"
                aria-checked={selected}
                aria-label={`${d.month}월 ${d.day}일 ${d.weekday}`}
                onClick={() => setDayKey(d.key)}
                className={`flex h-15 w-10 flex-col items-center justify-center gap-0.5 rounded-xl ${
                  selected ? 'bg-doctor text-white' : 'border border-line bg-white text-ink'
                }`}
              >
                <span className={`text-xs font-medium ${selected ? 'text-white' : 'text-ink-muted'}`}>{d.weekday}</span>
                <span className="text-base font-bold">{d.day}</span>
              </button>
            )
          })}
        </div>
        <dl className="grid grid-cols-3 rounded-2xl bg-doctor-soft py-3 text-center text-doctor">
          {[
            ['예약', list.filter((a) => a.status !== 'cancelled').length],
            ['진료 완료', count('completed')],
            ['취소', count('cancelled')],
          ].map(([label, value]) => (
            <div key={label} className="flex flex-col-reverse">
              <dt className="text-xs">{label}</dt>
              <dd className="text-lg font-bold">{value}</dd>
            </div>
          ))}
        </dl>
      </div>

      <div className="flex flex-1 flex-col gap-2.5 p-5">
        {schedule.isPending && <LoadingState />}
        {schedule.isError && <ErrorState message={schedule.error.message} onRetry={schedule.refetch} />}
        {schedule.isSuccess && list.length === 0 && <EmptyState title="이 날은 예약이 없어요" />}
        {list.map((a) => {
          const status = APPOINTMENT_STATUS[a.status]
          const who = [a.subject_name, [ageGroup(a.subject_birth_year), genderLabel(a.subject_gender)].filter(Boolean).join(' '), VISIT_TYPE[a.visit_type]]
          return (
            <Link key={a.id} to={`/doctor/appointments/${a.id}`} className="flex flex-col gap-2 rounded-2xl bg-white p-4">
              <span className="flex items-center justify-between">
                <span className="text-[17px] font-bold text-doctor">{formatSlot(a.start_at).split(' ').pop()}</span>
                <Pill tone={a.status === 'booked' ? 'doctor' : status.tone}>{status.label}</Pill>
              </span>
              <span className="text-[15px] font-bold">{who.filter(Boolean).join(' · ')}</span>
              {a.symptom_note && <span className="line-clamp-2 text-[13px] text-ink-muted">{a.symptom_note}</span>}
            </Link>
          )
        })}
      </div>
    </div>
  )
}
