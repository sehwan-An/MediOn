// 질문 상태. 빨강·초록 대신 주황(대기)·파랑(도착)
export default function StatusBadge({ status }) {
  const answered = status === 'answered'
  return (
    <span
      className={`inline-flex rounded-md px-2 py-0.5 text-xs font-bold ${
        answered ? 'bg-done-soft text-done' : 'bg-wait-soft text-wait'
      }`}
    >
      {answered ? '답변 도착' : '답변 대기'}
    </span>
  )
}
