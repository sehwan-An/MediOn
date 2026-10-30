import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getQuestions } from '../../api/questions'
import { DEPARTMENTS } from '../../constants/departments'
import useAuth from '../../context/useAuth'
import useLoginPrompt from '../../context/useLoginPrompt'
import PageHeader from '../../components/layout/PageHeader'
import QuestionCard from '../../components/question/QuestionCard'
import Button from '../../components/ui/Button'
import Chip from '../../components/ui/Chip'
import Icon from '../../components/ui/Icon'
import { EmptyState, ErrorState, LoadingState } from '../../components/ui/States'

// 상담 피드 (C-1~C-3): 의사가 답변한 공개 질문, 최신순. 진료 분야 칩 + 키워드 검색
export default function QnaFeedPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { requireLogin } = useLoginPrompt()
  const [department, setDepartment] = useState(null)
  const [input, setInput] = useState('')
  const [keyword, setKeyword] = useState('')
  const list = useQuery({
    queryKey: ['questions', department, keyword],
    queryFn: () => getQuestions({ department: department ?? undefined, q: keyword || undefined }),
  })

  const ask = () => {
    if (!user) return requireLogin({ from: '/questions/new', message: '질문하려면 로그인해주세요.\n로그인하면 질문 작성으로 이어가요.' })
    navigate('/questions/new')
  }

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader title="상담" />
      <div className="flex flex-col gap-3 bg-white px-5 pb-3">
        <form role="search" onSubmit={(e) => { e.preventDefault(); setKeyword(input.trim()) }}
          className="flex h-11 items-center gap-2 rounded-xl bg-surface px-3.5">
          <Icon name="search" size={18} className="text-ink-muted" />
          <input type="search" aria-label="질문 검색" placeholder="증상으로 검색 (예: 기침)" value={input}
            onChange={(e) => setInput(e.target.value)} className="flex-1 bg-transparent text-[15px] outline-none placeholder:text-ink-muted" />
        </form>
        <div className="-mx-5 flex gap-2 overflow-x-auto px-5">
          <Chip selected={department === null} onClick={() => setDepartment(null)}>전체</Chip>
          {DEPARTMENTS.map((d) => (
            <Chip key={d.code} selected={department === d.code} onClick={() => setDepartment(d.code)}>{d.name}</Chip>
          ))}
        </div>
      </div>

      <div className="flex flex-1 flex-col gap-3 p-5">
        {list.isPending && <LoadingState />}
        {list.isError && <ErrorState message={list.error.message} onRetry={list.refetch} />}
        {list.isSuccess && list.data.length === 0 && (
          <EmptyState title={keyword ? `'${keyword}' 질문이 없어요` : '아직 답변이 달린 질문이 없어요'} description="궁금한 증상을 의사에게 직접 물어보세요" />
        )}
        {list.data?.map((q) => <QuestionCard key={q.id} question={q} to={`/questions/${q.id}`} />)}
      </div>

      <div className="sticky bottom-16 flex justify-end px-5 pb-3">
        <Button className="shadow-lg" onClick={ask}>
          <Icon name="plus" size={18} /> 질문하기
        </Button>
      </div>
    </div>
  )
}
