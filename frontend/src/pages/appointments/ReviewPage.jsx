import { useState } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createReview, getAppointment } from '../../api/appointments'
import { REVIEW_TAGS } from '../../constants/appointments'
import TopBar from '../../components/layout/TopBar'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Chip from '../../components/ui/Chip'
import { ErrorState, LoadingState } from '../../components/ui/States'

const MAX_BODY = 500

// 진료 후기 작성 (N-1). 결제까지 끝난 진료에 한 번만. 닉네임은 가운데를 가려서 보여준다
export default function ReviewPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [wantsRevisit, setWantsRevisit] = useState(null)
  const [tags, setTags] = useState([])
  const [body, setBody] = useState('')
  const [error, setError] = useState('')
  const appointment = useQuery({ queryKey: ['appointment', id], queryFn: () => getAppointment(id) })

  const submit = useMutation({
    mutationFn: () => createReview(id, { wants_revisit: wantsRevisit, tags, body }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointment', id] })
      queryClient.invalidateQueries({ queryKey: ['doctor'] })
      queryClient.invalidateQueries({ queryKey: ['doctor-reviews'] })
      queryClient.invalidateQueries({ queryKey: ['doctors'] })
      navigate(`/appointments/${id}`, { replace: true })
    },
    onError: (e) => setError(e.message),
  })

  if (appointment.isPending) return <><TopBar title="후기 작성" /><LoadingState /></>
  if (appointment.isError) return <><TopBar title="후기 작성" /><ErrorState message={appointment.error.message} /></>
  const a = appointment.data
  if (a.has_review || a.payment_status !== 'paid') return <Navigate to={`/appointments/${id}`} replace />

  const toggleTag = (value) => setTags((t) => (t.includes(value) ? t.filter((v) => v !== value) : [...t, value]))
  const handleSubmit = () => {
    if (wantsRevisit === null) return setError('다시 진료받고 싶은지 골라주세요')
    setError('')
    submit.mutate()
  }

  return (
    <div className="flex flex-1 flex-col">
      <TopBar title="후기 작성" />
      <div className="flex flex-col gap-3 p-5">
        <Card>
          <h2 className="text-[17px] font-bold">{a.doctor.name} 의사에게 다시 진료받고 싶으세요?</h2>
          <div role="radiogroup" aria-label="재진 희망" className="grid grid-cols-2 gap-2">
            {[[true, '네, 다시 받을래요'], [false, '아니요']].map(([value, label]) => (
              <button key={label} type="button" role="radio" aria-checked={wantsRevisit === value}
                onClick={() => setWantsRevisit(value)}
                className={`min-h-12 rounded-[14px] text-[15px] ${wantsRevisit === value ? 'border-2 border-primary bg-primary-soft font-bold text-primary' : 'border border-line bg-white font-medium'}`}>
                {label}
              </button>
            ))}
          </div>
        </Card>
        <Card>
          <h2 className="text-[17px] font-bold">좋았던 점 <span className="text-sm font-normal text-ink-muted">여러 개 선택</span></h2>
          <div className="flex flex-wrap gap-2">
            {REVIEW_TAGS.map((t) => (
              <Chip key={t.value} selected={tags.includes(t.value)} onClick={() => toggleTag(t.value)}>{t.label}</Chip>
            ))}
          </div>
        </Card>
        <Card>
          <label htmlFor="review-body" className="text-[17px] font-bold">
            후기 <span className="text-sm font-normal text-ink-muted">선택</span>
          </label>
          <textarea id="review-body" rows={4} maxLength={MAX_BODY} value={body} onChange={(e) => setBody(e.target.value)}
            placeholder="진료 경험을 자유롭게 남겨주세요. 개인정보나 진단명은 적지 말아주세요"
            className="w-full resize-none rounded-[14px] border border-line px-4 py-3 text-[15px] outline-none placeholder:text-ink-muted focus:border-primary" />
          <p className="text-right text-xs text-ink-muted">{body.length}/{MAX_BODY}</p>
        </Card>
      </div>
      <div className="sticky bottom-0 mt-auto flex flex-col gap-2 border-t border-line bg-white px-5 pt-3 pb-6">
        {error && <p role="alert" className="text-[13px] text-wait">{error}</p>}
        <Button className="w-full" disabled={submit.isPending} onClick={handleSubmit}>
          {submit.isPending ? '등록하는 중…' : '후기 등록하기'}
        </Button>
      </div>
    </div>
  )
}
