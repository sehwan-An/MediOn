import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toggleHelpful } from '../../api/answers'
import { deleteQuestion, getQuestion } from '../../api/questions'
import { departmentName } from '../../constants/departments'
import { durationLabel, QUESTION_STATUS } from '../../constants/questions'
import useAuth from '../../context/useAuth'
import useLoginPrompt from '../../context/useLoginPrompt'
import { ageGroup, formatDateTime, genderLabel } from '../../utils/format'
import TopBar from '../../components/layout/TopBar'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Icon from '../../components/ui/Icon'
import Pill from '../../components/ui/Pill'
import { ErrorState, LoadingState } from '../../components/ui/States'

// 질문 상세 (C-4~C-7): 질문 요약 + 의사 답변 카드, 도움돼요, 이 의사에게 진료 예약
export default function QuestionDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const { requireLogin } = useLoginPrompt()
  const [confirming, setConfirming] = useState(false)
  const question = useQuery({ queryKey: ['question', id], queryFn: () => getQuestion(id) })

  const helpful = useMutation({
    mutationFn: toggleHelpful,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['question', id] }),
  })
  const remove = useMutation({
    mutationFn: () => deleteQuestion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-questions'] })
      queryClient.invalidateQueries({ queryKey: ['questions'] })
      navigate(-1)
    },
  })

  if (question.isPending) return <><TopBar title="질문" /><LoadingState /></>
  if (question.isError) return <><TopBar title="질문" /><ErrorState message={question.error.message} /></>
  const q = question.data
  const status = QUESTION_STATUS[q.status]
  const meta = [ageGroup(q.author_birth_year), genderLabel(q.author_gender), q.body_part, durationLabel(q.duration)].filter(Boolean)

  const pressHelpful = (answerId) => {
    if (!user) return requireLogin({ from: `/questions/${id}`, message: '도움돼요를 누르려면 로그인해주세요.' })
    helpful.mutate(answerId)
  }
  // C-7: 질문 내용을 증상 메모로 가져가서 이 의사에게 예약
  const bookWith = (doctorId) => navigate(`/doctors/${doctorId}?question=${q.id}`)

  return (
    <div className="flex flex-1 flex-col">
      <TopBar title="질문" />
      <div className="flex flex-col gap-3 p-5">
        <p role="note" className="flex gap-2 rounded-xl bg-wait-soft px-3.5 py-3 text-[13px] font-medium text-wait">
          <Icon name="info" size={18} className="shrink-0" />
          의사 답변은 일반적인 건강 정보이며 진단·처방을 대신하지 않아요. 정확한 진료는 비대면 진료나 병원에서 받아주세요.
        </p>

        <Card>
          <span className="flex flex-wrap items-center gap-1.5">
            <Pill>{departmentName(q.department_code)}</Pill>
            <Pill tone={status.tone}>{status.label}</Pill>
            {q.visibility === 'private' && <Pill>비공개</Pill>}
          </span>
          <h2 className="text-xl font-bold">{q.title}</h2>
          {meta.length > 0 && <p className="text-[13px] text-ink-muted">{meta.join(' · ')}</p>}
          <p className="text-[15px] whitespace-pre-line">{q.body}</p>
          <p className="text-xs text-ink-muted">{formatDateTime(q.created_at)}</p>
        </Card>

        <h3 className="mt-2 text-[17px] font-bold">의사 답변 {q.answer_count}</h3>
        {q.answers.length === 0 && (
          <p className="rounded-[18px] bg-white px-[18px] py-6 text-center text-sm text-ink-muted">의사 답변을 기다리고 있어요. 답변이 오면 알림으로 알려드려요</p>
        )}
        {q.answers.map((a) => (
          <Card key={a.id} as="article">
            <div className="flex items-center gap-3">
              <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-doctor-soft font-bold text-doctor">{a.doctor.name.slice(0, 1)}</span>
              <span className="flex flex-col">
                <span className="flex items-center gap-1 text-[15px] font-bold">
                  {a.doctor.name} 의사 <Icon name="verified" size={16} className="text-primary" />
                </span>
                <span className="text-xs text-ink-muted">{departmentName(a.doctor.department_code)} · {a.doctor.hospital_name}</span>
              </span>
            </div>
            {a.recommends_visit && (
              <p className="rounded-xl border border-wait bg-wait-soft px-3.5 py-3 text-[13px] font-bold text-wait">
                대면 진료를 권해요 · {a.recommended_departments.map(departmentName).join(', ')}
              </p>
            )}
            <p className="text-[15px] whitespace-pre-line">{a.body}</p>
            <div className="flex items-center justify-between gap-2">
              <button type="button" aria-pressed={a.helped} disabled={helpful.isPending} onClick={() => pressHelpful(a.id)}
                className={`flex min-h-11 items-center gap-1.5 rounded-full px-3.5 text-[13px] font-bold ${a.helped ? 'bg-primary text-white' : 'bg-surface text-ink-muted'}`}>
                <Icon name="checkMark" size={16} /> 도움돼요 {a.helpful_count}
              </button>
              <span className="text-xs text-ink-muted">{formatDateTime(a.created_at)}</span>
            </div>
            {(!user || user.role === 'patient') && (
              <Button variant="soft" className="w-full" onClick={() => bookWith(a.doctor.id)}>
                이 의사에게 비대면 진료 받기
              </Button>
            )}
          </Card>
        ))}

        {q.is_mine && !confirming && (
          <Button variant="secondary" className="mt-2 w-full" onClick={() => setConfirming(true)}>질문 삭제하기</Button>
        )}
        {q.is_mine && confirming && (
          <div role="alert" className="mt-2 flex flex-col gap-2 rounded-[18px] bg-white p-[18px]">
            <p className="text-[15px] font-bold">질문을 삭제할까요? 의사 답변도 함께 지워져요</p>
            <div className="grid grid-cols-2 gap-2">
              <Button variant="secondary" onClick={() => setConfirming(false)}>취소</Button>
              <Button disabled={remove.isPending} onClick={() => remove.mutate()}>삭제하기</Button>
            </div>
          </div>
        )}
        {remove.isError && <p role="alert" className="text-[13px] text-wait">{remove.error.message}</p>}
      </div>
    </div>
  )
}
