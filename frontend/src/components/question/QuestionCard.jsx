import { Link } from 'react-router-dom'
import { QUESTION_STATUS, waitedFor } from '../../constants/questions'
import { departmentName } from '../../constants/departments'
import { formatDateTime } from '../../utils/format'
import Pill from '../ui/Pill'

// 질문 목록 한 줄 (상담 피드 · 내 질문 · 의사 질문함). showWaited: 의사 질문함에서 기다린 시간 표시
export default function QuestionCard({ question: q, to, showWaited = false }) {
  const status = QUESTION_STATUS[q.status]
  return (
    <Link to={to} className="flex flex-col gap-2 rounded-[18px] bg-white p-[18px]">
      <span className="flex items-center gap-1.5">
        <Pill>{departmentName(q.department_code)}</Pill>
        {showWaited ? <Pill tone="wait">{waitedFor(q.created_at)} 대기</Pill> : <Pill tone={status.tone}>{status.label}</Pill>}
        {q.visibility === 'private' && <Pill tone="muted">비공개</Pill>}
      </span>
      <span className="text-base font-bold">{q.title}</span>
      <span className="line-clamp-2 text-sm text-ink-muted">{q.body}</span>
      <span className="flex justify-between text-xs text-ink-muted">
        <span>{formatDateTime(q.created_at).slice(0, 10)}</span>
        {q.answer_count > 0 && <span className="font-bold text-primary">의사 답변 {q.answer_count}</span>}
      </span>
    </Link>
  )
}
