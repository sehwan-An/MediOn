import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getDoctorInbox } from '../../api/answers'
import PageHeader from '../../components/layout/PageHeader'
import QuestionCard from '../../components/question/QuestionCard'
import { EmptyState, ErrorState, LoadingState } from '../../components/ui/States'

// 의사 질문함 (D-1, D-2): 답변이 없는 질문을 오래 기다린 순으로. 내 전문 분야만 보기 토글
export default function DoctorInboxPage() {
  const [mineOnly, setMineOnly] = useState(false)
  const list = useQuery({ queryKey: ['doctor-inbox', mineOnly], queryFn: () => getDoctorInbox({ mine_only: mineOnly }) })

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader title="질문함" />
      <label className="flex min-h-12 items-center justify-between bg-white px-5 text-[15px] font-medium">
        내 전문 분야만 보기
        <input type="checkbox" role="switch" className="size-5 accent-doctor" checked={mineOnly} onChange={(e) => setMineOnly(e.target.checked)} />
      </label>
      <div className="flex flex-1 flex-col gap-3 p-5">
        {list.isPending && <LoadingState />}
        {list.isError && <ErrorState message={list.error.message} onRetry={list.refetch} />}
        {list.isSuccess && list.data.length === 0 && <EmptyState title="답변을 기다리는 질문이 없어요" />}
        {list.data?.map((q) => <QuestionCard key={q.id} question={q} to={`/doctor/questions/${q.id}/answer`} showWaited />)}
      </div>
    </div>
  )
}
