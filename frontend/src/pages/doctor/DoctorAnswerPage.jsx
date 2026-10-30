import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createAnswer } from '../../api/answers'
import { getQuestion } from '../../api/questions'
import { DEPARTMENTS, departmentName } from '../../constants/departments'
import { durationLabel } from '../../constants/questions'
import { ageGroup, formatDateTime, genderLabel } from '../../utils/format'
import TopBar from '../../components/layout/TopBar'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Chip from '../../components/ui/Chip'
import Icon from '../../components/ui/Icon'
import Pill from '../../components/ui/Pill'
import { ErrorState, LoadingState } from '../../components/ui/States'

const BODY_MAX = 2000

// 답변 작성 (D-3, D-4): 질문을 보면서 답변. 대면 진료 권유를 켜면 추천 진료과를 고른다
// 이미 답변한 질문이면 내 답변과 다른 의사 답변을 보여준다
export default function DoctorAnswerPage() {
  const { id } = useParams()
  const queryClient = useQueryClient()
  const [body, setBody] = useState('')
  const [recommends, setRecommends] = useState(false)
  const [departments, setDepartments] = useState([])
  const [error, setError] = useState('')
  const question = useQuery({ queryKey: ['question', id], queryFn: () => getQuestion(id) })

  const submit = useMutation({
    mutationFn: () => createAnswer(id, { body, recommends_visit: recommends, recommended_departments: recommends ? departments : [] }),
    onSuccess: (data) => {
      queryClient.setQueryData(['question', id], data)
      queryClient.invalidateQueries({ queryKey: ['doctor-inbox'] })
      queryClient.invalidateQueries({ queryKey: ['doctor-answers'] })
    },
    onError: (e) => setError(e.message),
  })

  if (question.isPending) return <><TopBar title="답변 작성" /><LoadingState /></>
  if (question.isError) return <><TopBar title="답변 작성" /><ErrorState message={question.error.message} /></>
  const q = question.data
  const meta = [ageGroup(q.author_birth_year), genderLabel(q.author_gender), q.body_part, durationLabel(q.duration)].filter(Boolean)

  const toggleDept = (code) =>
    setDepartments((list) => (list.includes(code) ? list.filter((c) => c !== code) : list.length < 3 ? [...list, code] : list))
  const handleSubmit = () => {
    if (!body.trim()) return setError('답변을 입력해주세요')
    if (recommends && departments.length === 0) return setError('대면 진료를 권할 진료과를 골라주세요')
    setError('')
    submit.mutate()
  }

  return (
    <div className="flex flex-1 flex-col">
      <TopBar title={q.answered_by_me ? '내 답변' : '답변 작성'} />
      <div className="flex flex-col gap-3 p-5">
        <Card>
          <span className="flex flex-wrap gap-1.5">
            <Pill tone="doctor">{departmentName(q.department_code)}</Pill>
            {q.visibility === 'private' && <Pill>비공개</Pill>}
          </span>
          <h2 className="text-lg font-bold">{q.title}</h2>
          {meta.length > 0 && <p className="text-[13px] text-ink-muted">{meta.join(' · ')}</p>}
          <p className="text-[15px] whitespace-pre-line">{q.body}</p>
          <p className="text-xs text-ink-muted">{formatDateTime(q.created_at)}</p>
        </Card>

        {q.answers.map((a) => (
          <Card key={a.id} as="article" className="gap-2">
            <p className="text-sm font-bold">{a.doctor.name} 의사 · {departmentName(a.doctor.department_code)}</p>
            {a.recommends_visit && (
              <p className="text-[13px] font-bold text-wait">대면 진료 권유 · {a.recommended_departments.map(departmentName).join(', ')}</p>
            )}
            <p className="text-sm whitespace-pre-line">{a.body}</p>
            <p className="text-xs text-ink-muted">도움돼요 {a.helpful_count}</p>
          </Card>
        ))}

        {!q.answered_by_me && (
          <>
            <div className="flex flex-col gap-2">
              <label htmlFor="answer-body" className="text-[17px] font-bold">답변</label>
              <div className="flex flex-col gap-2 rounded-[14px] border border-line bg-white px-4 py-3.5 focus-within:border-doctor">
                <textarea id="answer-body" rows={7} maxLength={BODY_MAX} value={body} onChange={(e) => setBody(e.target.value)}
                  placeholder="일반적인 안내로 작성해주세요. 진단명이나 처방은 적지 않아요"
                  className="resize-none text-[15px] outline-none placeholder:text-ink-muted" />
                <span className="self-end text-xs text-ink-muted">{body.length} / {BODY_MAX}</span>
              </div>
            </div>
            <label className="flex min-h-12 items-center justify-between rounded-[14px] bg-white px-4 text-[15px] font-bold">
              대면 진료 권유
              <input type="checkbox" role="switch" className="size-5 accent-doctor" checked={recommends} onChange={(e) => setRecommends(e.target.checked)} />
            </label>
            {recommends && (
              <fieldset className="flex flex-col gap-2">
                <legend className="mb-2 text-sm font-bold">추천 진료과 <span className="font-normal text-ink-muted">최대 3개</span></legend>
                <div className="flex flex-wrap gap-2">
                  {DEPARTMENTS.map((d) => (
                    <Chip key={d.code} tone="doctor" selected={departments.includes(d.code)} onClick={() => toggleDept(d.code)}>{d.name}</Chip>
                  ))}
                </div>
              </fieldset>
            )}
            <p className="flex gap-2 rounded-xl bg-doctor-soft px-3.5 py-3 text-[13px] font-medium text-doctor">
              <Icon name="info" size={18} className="shrink-0" />
              답변은 환자에게 "진단·처방을 대신하지 않음" 안내와 함께 보여요
            </p>
          </>
        )}
      </div>
      {!q.answered_by_me && (
        <div className="sticky bottom-0 mt-auto flex flex-col gap-2 border-t border-line bg-white px-5 pt-3 pb-6">
          {error && <p role="alert" className="text-[13px] text-wait">{error}</p>}
          <Button variant="doctor" className="w-full" disabled={submit.isPending} onClick={handleSubmit}>
            {submit.isPending ? '등록하는 중…' : '답변 등록하기'}
          </Button>
        </div>
      )}
    </div>
  )
}
