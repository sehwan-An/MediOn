import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getSlots } from '../../api/doctors'
import { upcomingDays } from '../../utils/format'
import { ErrorState, LoadingState } from '../ui/States'

// 예약 날짜·시간 선택 (H-6). 오늘부터 7일, 30분 단위. 지난 시간·점심시간·진료 없는 요일은 고를 수 없다
// value: 고른 슬롯의 start_at (UTC ISO), onChange(start_at | null)
export default function SlotPicker({ doctorId, schedules, value, onChange }) {
  const [days] = useState(() => upcomingDays(7))
  const openWeekdays = new Set(schedules.map((s) => s.weekday))
  const [dayKey, setDayKey] = useState(() => (days.find((d) => openWeekdays.has(d.scheduleWeekday)) ?? days[0]).key)

  const slotsQuery = useQuery({ queryKey: ['slots', doctorId, dayKey], queryFn: () => getSlots(doctorId, dayKey) })

  const pickDay = (key) => {
    setDayKey(key)
    onChange(null)
  }

  const slots = slotsQuery.data?.slots ?? []
  const morning = slots.filter((s) => s.label < '12:00')
  const afternoon = slots.filter((s) => s.label >= '12:00')
  const lunch = schedules.find((s) => s.weekday === days.find((d) => d.key === dayKey)?.scheduleWeekday)

  return (
    <div className="flex flex-col gap-3">
      <div className="flex justify-between" role="radiogroup" aria-label="예약 날짜">
        {days.map((d) => {
          const off = !openWeekdays.has(d.scheduleWeekday)
          const selected = d.key === dayKey
          let look = 'border border-line bg-white text-ink'
          if (off) look = 'bg-surface text-ink-muted'
          if (selected) look = 'bg-primary text-white'
          return (
            <button
              key={d.key}
              type="button"
              role="radio"
              aria-checked={selected}
              aria-label={`${d.month}월 ${d.day}일 ${d.weekday}${off ? ' 휴진' : ''}`}
              disabled={off}
              onClick={() => pickDay(d.key)}
              className={`flex h-15 w-10 flex-col items-center justify-center gap-0.5 rounded-xl ${look}`}
            >
              <span className={`text-xs font-medium ${selected ? 'text-white' : 'text-ink-muted'}`}>{d.weekday}</span>
              <span className="text-base font-bold">{d.day}</span>
            </button>
          )
        })}
      </div>

      {slotsQuery.isPending && <LoadingState message="예약 가능한 시간을 불러오는 중이에요" />}
      {slotsQuery.isError && <ErrorState message={slotsQuery.error.message} onRetry={slotsQuery.refetch} />}
      {slotsQuery.isSuccess && !slots.some((s) => s.available) && (
        <p className="rounded-xl bg-surface px-4 py-6 text-center text-sm text-ink-muted">
          {slotsQuery.data.closed ? '이 날은 진료하지 않아요' : '이 날은 예약할 수 있는 시간이 없어요'}
        </p>
      )}
      {slotsQuery.isSuccess && slots.some((s) => s.available) && (
        <>
          <SlotGroup title="오전" slots={morning} value={value} onChange={onChange} />
          <SlotGroup
            title={lunch?.lunch_start ? `오후 · 점심시간 ${lunch.lunch_start.slice(0, 5)}~${lunch.lunch_end.slice(0, 5)} 제외` : '오후'}
            slots={afternoon}
            value={value}
            onChange={onChange}
          />
        </>
      )}
    </div>
  )
}

function SlotGroup({ title, slots, value, onChange }) {
  if (slots.length === 0) return null
  return (
    <div className="flex flex-col gap-2">
      <p className="text-[13px] font-bold text-ink-muted">{title}</p>
      <div className="grid grid-cols-4 gap-2" role="radiogroup" aria-label={`${title} 시간`}>
        {slots.map((slot) => {
          const selected = slot.start_at === value
          let look = 'border border-line bg-white font-medium text-ink'
          if (!slot.available) look = 'bg-surface text-ink-muted line-through'
          if (selected) look = 'bg-primary font-bold text-white'
          return (
            <button
              key={slot.start_at}
              type="button"
              role="radio"
              aria-checked={selected}
              disabled={!slot.available}
              onClick={() => onChange(slot.start_at)}
              className={`h-10 rounded-[10px] text-sm ${look}`}
            >
              {slot.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}
