import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createQuestion } from '../../api/questions'
import { DEPARTMENTS } from '../../constants/departments'
import { BODY_MAX, DURATIONS, TITLE_MAX } from '../../constants/questions'
import TopBar from '../../components/layout/TopBar'
import Button from '../../components/ui/Button'
import Chip from '../../components/ui/Chip'
import Icon from '../../components/ui/Icon'
import TextField from '../../components/ui/TextField'

// 질문하기 (B-1, B-2). 사진 첨부(B-3)·임시저장(B-4)은 아직 없다
export default function QuestionWritePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [form, setForm] = useState({ department: undefined, title: '', body: '', bodyPart: '', duration: null, visibility: 'public' })
  const [errors, setErrors] = useState({})

  const mutation = useMutation({
    mutationFn: createQuestion,
    onSuccess: (q) => {
      queryClient.invalidateQueries({ queryKey: ['my-questions'] })
      navigate(`/questions/${q.id}`, { replace: true })
    },
    onError: (e) => setErrors({ form: e.message }),
  })

  const set = (key, value) => setForm((f) => ({ ...f, [key]: value }))

  const handleSubmit = (event) => {
    event.preventDefault()
    const next = {}
    if (form.department === undefined) next.department = '진료 분야를 골라주세요'
    if (!form.title.trim()) next.title = '제목을 입력해주세요'
    if (!form.body.trim()) next.body = '증상 설명을 입력해주세요'
    if (!form.duration) next.duration = '언제부터 불편했는지 골라주세요'
    setErrors(next)
    if (Object.keys(next).length > 0) return
    mutation.mutate({
      department_code: form.department, title: form.title, body: form.body,
      body_part: form.bodyPart || null, duration: form.duration, visibility: form.visibility,
    })
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="flex flex-1 flex-col">
      <TopBar title="질문하기" />
      <div className="flex flex-col gap-5 p-5">
        <fieldset className="flex flex-col gap-2">
          <legend className="mb-2 text-sm font-bold">진료 분야</legend>
          <div className="flex flex-wrap gap-2">
            {DEPARTMENTS.map((d) => (
              <Chip key={d.code} selected={form.department === d.code} onClick={() => set('department', d.code)}>{d.name}</Chip>
            ))}
            <Chip selected={form.department === null} onClick={() => set('department', null)}>잘 모르겠어요</Chip>
          </div>
          {errors.department && <p className="text-[13px] text-wait">{errors.department}</p>}
        </fieldset>

        <TextField label="제목" placeholder="예: 2주째 마른기침이 나요" maxLength={TITLE_MAX}
          value={form.title} onChange={(e) => set('title', e.target.value)} error={errors.title} />

        <div className="flex flex-col gap-2">
          <label htmlFor="question-body" className="text-sm font-bold">증상 설명</label>
          <div className={`flex flex-col gap-2 rounded-[14px] border bg-white px-4 py-3.5 focus-within:border-primary ${errors.body ? 'border-wait' : 'border-line'}`}>
            <textarea id="question-body" rows={6} maxLength={BODY_MAX} value={form.body} onChange={(e) => set('body', e.target.value)}
              placeholder="어디가, 어떻게, 언제 불편한지 적어주세요. 이름·연락처 같은 개인정보는 적지 마세요"
              aria-describedby="question-body-count" className="resize-none text-[15px] outline-none placeholder:text-ink-muted" />
            <span id="question-body-count" className="self-end text-xs text-ink-muted">{form.body.length} / {BODY_MAX}</span>
          </div>
          {errors.body && <p className="text-[13px] text-wait">{errors.body}</p>}
        </div>

        <TextField label="불편한 부위" optional placeholder="예: 목, 허리" maxLength={30}
          value={form.bodyPart} onChange={(e) => set('bodyPart', e.target.value)} />

        <fieldset className="flex flex-col gap-2">
          <legend className="mb-2 text-sm font-bold">언제부터 불편했나요?</legend>
          <div className="grid grid-cols-2 gap-2">
            {DURATIONS.map((d) => (
              <Chip key={d.value} selected={form.duration === d.value} onClick={() => set('duration', d.value)}>{d.label}</Chip>
            ))}
          </div>
          {errors.duration && <p className="text-[13px] text-wait">{errors.duration}</p>}
        </fieldset>

        <fieldset className="flex flex-col gap-2">
          <legend className="mb-2 text-sm font-bold">공개 범위</legend>
          {[['public', '공개', '답변이 달리면 상담 피드에 보여요 (닉네임은 안 보여요)'], ['private', '비공개', '나와 의사만 볼 수 있어요']].map(([value, label, desc]) => (
            <label key={value} className={`flex min-h-14 items-center gap-3 rounded-[14px] px-4 py-2.5 ${form.visibility === value ? 'border-2 border-primary bg-primary-soft' : 'border border-line bg-white'}`}>
              <input type="radio" name="visibility" className="size-5 accent-primary" checked={form.visibility === value} onChange={() => set('visibility', value)} />
              <span className="flex flex-col">
                <span className="text-[15px] font-bold">{label}</span>
                <span className="text-xs text-ink-muted">{desc}</span>
              </span>
            </label>
          ))}
        </fieldset>

        <p className="flex gap-2 rounded-xl bg-wait-soft px-3.5 py-3 text-[13px] font-medium text-wait">
          <Icon name="info" size={18} className="shrink-0" />
          의사 답변은 일반적인 안내이며 진단·처방을 대신하지 않아요. 급한 증상은 119 또는 가까운 응급실로 가세요.
        </p>
      </div>
      <div className="sticky bottom-0 mt-auto flex flex-col gap-2 border-t border-line bg-white px-5 pt-3 pb-6">
        {errors.form && <p role="alert" className="text-[13px] text-wait">{errors.form}</p>}
        <Button type="submit" className="w-full" disabled={mutation.isPending}>
          {mutation.isPending ? '등록하는 중…' : '질문 등록하기'}
        </Button>
      </div>
    </form>
  )
}
