import { SCHEDULE_WEEKDAYS, hhmm } from '../../utils/format'

// 요일별 진료 시간표 (I-1). 의사 상세와 의사의 진료 시간표 화면에서 같이 쓴다
export default function ScheduleList({ schedules }) {
  return (
    <dl className="flex flex-col">
      {SCHEDULE_WEEKDAYS.map((label, weekday) => {
        const s = schedules.find((x) => x.weekday === weekday)
        return (
          <div key={label} className="flex items-center gap-3 py-2 text-sm">
            <dt className={`w-6 font-bold ${s ? 'text-ink' : 'text-ink-muted'}`}>{label}</dt>
            <dd className="flex flex-1 items-center justify-between gap-2">
              <span className={s ? 'font-medium' : 'text-ink-muted'}>
                {s ? `${hhmm(s.start_time)} ~ ${hhmm(s.end_time)}` : '휴진'}
              </span>
              {s?.lunch_start && (
                <span className="text-xs text-ink-muted">
                  점심 {hhmm(s.lunch_start)} ~ {hhmm(s.lunch_end)}
                </span>
              )}
            </dd>
          </div>
        )
      })}
    </dl>
  )
}
