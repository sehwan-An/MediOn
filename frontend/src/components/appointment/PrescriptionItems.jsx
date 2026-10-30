import Icon from '../ui/Icon'

// 처방 약 목록 (피그마 Drug Row). onRemove 가 있으면 삭제 버튼을 보여준다 (처방전 작성 화면)
export default function PrescriptionItems({ prescription, onRemove }) {
  return (
    <ul className="flex flex-col">
      {prescription.items.map((item, index) => (
        <li key={`${item.drug.id}-${index}`} className="flex items-center gap-3 py-2.5">
          <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-primary-soft text-primary">
            <Icon name="pill" size={20} />
          </span>
          <span className="flex flex-1 flex-col">
            <span className="text-[15px] font-bold">{item.drug.name}</span>
            <span className="text-[13px] text-ink-muted">
              1회 {item.dose} · 1일 {item.times_per_day}회 · {item.days}일
            </span>
            {item.instruction && <span className="text-xs font-medium text-primary">{item.instruction}</span>}
          </span>
          {onRemove && (
            <button
              type="button"
              aria-label={`${item.drug.name} 빼기`}
              onClick={() => onRemove(index)}
              className="flex size-11 items-center justify-center text-ink-muted"
            >
              <Icon name="trash" size={20} />
            </button>
          )}
        </li>
      ))}
      {prescription.note && <li className="mt-1 rounded-xl bg-surface px-3.5 py-3 text-[13px]">{prescription.note}</li>}
    </ul>
  )
}
