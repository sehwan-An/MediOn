import { Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getCategories } from '../../api/doctors'
import { departmentName } from '../../constants/departments'
import useAuth from '../../context/useAuth'
import useLoginPrompt from '../../context/useLoginPrompt'
import MedicationCard from '../../components/home/MedicationCard'
import PageHeader from '../../components/layout/PageHeader'
import Icon from '../../components/ui/Icon'
import { ErrorState, LoadingState } from '../../components/ui/States'

// 홈: 오늘 약 복용(P-1), 질문하기(B-1), 증상 카테고리(H-1). 다가오는 진료 카드는 아직 없다
export default function HomePage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { requireLogin } = useLoginPrompt()
  const ask = () => {
    if (!user) return requireLogin({ from: '/questions/new', message: '질문하려면 로그인해주세요.\n로그인하면 질문 작성으로 이어가요.' })
    navigate('/questions/new')
  }
  const categories = useQuery({ queryKey: ['categories'], queryFn: getCategories, staleTime: Infinity })

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <span className="text-[22px] font-bold text-primary">MediON</span>
      </PageHeader>
      <div className="flex flex-1 flex-col gap-4 p-5">
        {user && <MedicationCard />}

        <section className="flex items-center gap-3 rounded-[18px] bg-primary p-[18px] text-white">
          <span className="flex flex-1 flex-col gap-0.5">
            <span className="text-[17px] font-bold">진료 전에 궁금한 게 있나요?</span>
            <span className="text-[13px] opacity-90">증상을 남기면 의사가 답변해드려요</span>
          </span>
          <button type="button" onClick={ask} className="flex min-h-11 shrink-0 items-center gap-1 rounded-xl bg-white px-4 text-[15px] font-bold text-primary">
            <Icon name="chat" size={18} /> 질문하기
          </button>
        </section>
        <Link to="/qna" className="-mt-2 flex min-h-11 items-center justify-between rounded-[14px] bg-white px-4 text-sm font-medium">
          다른 사람들의 질문과 의사 답변 보기
          <Icon name="chevronRight" size={18} className="text-ink-muted" />
        </Link>

        <div className="flex flex-col gap-1">
          <h1 className="text-xl font-bold">어디가 불편하세요?</h1>
          <p className="text-sm text-ink-muted">증상을 고르면 맞는 진료과 의사를 보여드려요</p>
        </div>
        {categories.isPending && <LoadingState />}
        {categories.isError && <ErrorState message={categories.error.message} onRetry={categories.refetch} />}
        {categories.isSuccess && (
          <ul className="grid grid-cols-2 gap-3">
            {categories.data.map((c) => (
              <li key={c.code}>
                <Link
                  to={`/doctors?category=${c.code}`}
                  className="flex h-24 flex-col justify-between rounded-2xl bg-white p-4"
                >
                  <span className="flex items-center justify-between">
                    <span className="text-base font-bold">{c.name}</span>
                    <Icon name="chevronRight" size={18} className="text-ink-muted" />
                  </span>
                  <span className="line-clamp-2 text-xs text-ink-muted">{c.departments.map(departmentName).join(' · ')}</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
