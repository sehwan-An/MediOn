import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getMyQuestions } from '../../api/questions'
import TopBar from '../../components/layout/TopBar'
import QuestionCard from '../../components/question/QuestionCard'
import { buttonClass } from '../../components/ui/buttonStyles'
import { EmptyState, ErrorState, LoadingState } from '../../components/ui/States'

const TABS = [
  { key: 'all', label: '전체' },
  { key: 'waiting', label: '답변 대기' },
  { key: 'answered', label: '답변 도착' },
]

// 내 질문 (B-5): 상태별 탭과 개수
export default function MyQuestionsPage() {
  const [tab, setTab] = useState('all')
  const list = useQuery({
    queryKey: ['my-questions', tab],
    queryFn: () => getMyQuestions(tab === 'all' ? {} : { status: tab }),
  })

  return (
    <div className="flex flex-1 flex-col">
      <TopBar title="내 질문" />
      <div role="tablist" className="grid grid-cols-3 bg-white px-5">
        {TABS.map((t) => (
          <button key={t.key} type="button" role="tab" aria-selected={tab === t.key} onClick={() => setTab(t.key)}
            className={`min-h-11 border-b-2 text-[15px] ${tab === t.key ? 'border-ink font-bold text-ink' : 'border-transparent font-medium text-ink-muted'}`}>
            {t.label} {list.data ? list.data.counts[t.key] : ''}
          </button>
        ))}
      </div>
      <div className="flex flex-1 flex-col gap-3 p-5">
        {list.isPending && <LoadingState />}
        {list.isError && <ErrorState message={list.error.message} onRetry={list.refetch} />}
        {list.isSuccess && list.data.items.length === 0 && (
          <EmptyState title="질문이 없어요" action={<Link to="/questions/new" className={buttonClass('primary')}>질문하기</Link>} />
        )}
        {list.data?.items.map((q) => <QuestionCard key={q.id} question={q} to={`/questions/${q.id}`} />)}
      </div>
    </div>
  )
}
