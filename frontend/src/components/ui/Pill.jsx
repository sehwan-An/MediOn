// 상태 표시 (피그마 Pill 컴포넌트). 빨강·초록 대신 주황(대기)·파랑(완료)
const TONES = {
  wait: 'bg-wait-soft text-wait',
  done: 'bg-done-soft text-done',
  muted: 'bg-surface text-ink-muted',
  doctor: 'bg-doctor-soft text-doctor',
  primary: 'bg-primary text-white',
}

export default function Pill({ tone = 'muted', children }) {
  return (
    <span className={`inline-flex shrink-0 items-center rounded-md px-2 py-0.5 text-xs font-bold ${TONES[tone] ?? TONES.muted}`}>
      {children}
    </span>
  )
}
