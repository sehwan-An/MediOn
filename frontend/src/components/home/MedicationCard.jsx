import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { checkMedication, getTodayMedications } from '../../api/medications'
import Icon from '../ui/Icon'

// 홈 "오늘 약 복용" (P-1, P-2). 약국에서 받은 처방이 있을 때만 보인다. 시간대를 눌러 먹었는지 체크
export default function MedicationCard() {
  const queryClient = useQueryClient()
  const plans = useQuery({ queryKey: ['medications-today'], queryFn: getTodayMedications })
  const check = useMutation({
    mutationFn: checkMedication,
    onSuccess: (data) => queryClient.setQueryData(['medications-today'], data),
  })

  // 복용 중인 약이 없거나 불러오지 못하면 홈을 가리지 않게 아무것도 안 그린다
  if (!plans.data?.length) return null

  return (
    <section aria-labelledby="medication-title" className="flex flex-col gap-3 rounded-[18px] bg-white p-[18px]">
      <h2 id="medication-title" className="flex items-center gap-2 text-[17px] font-bold">
        <Icon name="pill" size={20} className="text-primary" /> 오늘 약 복용
      </h2>
      {plans.data.map((p) => {
        const done = p.slots.filter((s) => s.taken).length
        return (
          <div key={p.prescription_id} className="flex flex-col gap-2.5">
            <Link to={`/appointments/${p.appointment_id}`} className="flex items-center justify-between text-[13px] text-ink-muted">
              <span>{p.doctor_name} 의사 처방 · {p.day}일째 / {p.total_days}일</span>
              <span className="font-bold text-primary">{done}/{p.slots.length} 완료</span>
            </Link>
            <ul className="flex flex-col gap-2">
              {p.slots.map((s) => (
                <li key={s.slot}>
                  <button
                    type="button"
                    aria-pressed={s.taken}
                    disabled={check.isPending}
                    onClick={() => check.mutate({ prescription_id: p.prescription_id, slot: s.slot, taken: !s.taken })}
                    className={`flex w-full items-center gap-3 rounded-[14px] px-3.5 py-3 text-left ${s.taken ? 'bg-primary-soft' : 'bg-surface'}`}
                  >
                    <span className={`flex size-6 shrink-0 items-center justify-center rounded-full ${s.taken ? 'bg-primary text-white' : 'border-2 border-line bg-white'}`}>
                      {s.taken && <Icon name="checkMark" size={14} />}
                    </span>
                    <span className="flex flex-1 flex-col">
                      <span className="text-[15px] font-bold">
                        {s.label} <span className="font-medium text-ink-muted">{s.time}</span>
                      </span>
                      <span className="text-[13px] text-ink-muted">
                        {s.drugs.map((d) => `${d.name} ${d.dose}`).join(', ')}
                      </span>
                    </span>
                    <span className={`text-[13px] font-bold ${s.taken ? 'text-primary' : 'text-ink-muted'}`}>{s.taken ? '먹었어요' : '체크'}</span>
                  </button>
                </li>
              ))}
            </ul>
            {p.note && <p className="text-[13px] text-ink-muted">복용 안내: {p.note}</p>}
          </div>
        )
      })}
      {check.isError && <p role="alert" className="text-[13px] text-wait">{check.error.message}</p>}
      <p className="text-xs text-ink-muted">시간은 권장 예시예요. 처방전의 복용 안내와 약사 설명을 따라주세요</p>
    </section>
  )
}
