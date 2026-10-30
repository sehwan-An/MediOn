import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getDoctorAnswers } from '../../api/answers'
import { formatDateTime } from '../../utils/format'
import TopBar from '../../components/layout/TopBar'
import Icon from '../../components/ui/Icon'
import { EmptyState, ErrorState, LoadingState } from '../../components/ui/States'

// 내 답변 (D-6): 내가 답변한 질문과 도움돼요 수
export default function DoctorAnswersPage() {
  const list = useQuery({ queryKey: ['doctor-answers'], queryFn: getDoctorAnswers })
  return (
    <div className="flex flex-1 flex-col">
      <TopBar title="내 답변" />
      <div className="flex flex-1 flex-col gap-3 p-5">
        {list.isPending && <LoadingState />}
        {list.isError && <ErrorState message={list.error.message} onRetry={list.refetch} />}
        {list.isSuccess && list.data.length === 0 && <EmptyState title="아직 답변한 질문이 없어요" />}
        {list.data?.map((a) => (
          <Link key={a.answer_id} to={`/doctor/questions/${a.question_id}/answer`} className="flex flex-col gap-1.5 rounded-[18px] bg-white p-[18px]">
            <span className="text-base font-bold">{a.question_title}</span>
            <span className="flex justify-between text-[13px] text-ink-muted">
              <span>{formatDateTime(a.created_at)}</span>
              <span className="flex items-center gap-1 font-bold text-doctor"><Icon name="checkMark" size={14} /> 도움돼요 {a.helpful_count}</span>
            </span>
          </Link>
        ))}
      </div>
    </div>
  )
}
