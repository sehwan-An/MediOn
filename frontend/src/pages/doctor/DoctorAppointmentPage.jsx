import { useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getDoctorAppointment, startConsultation } from '../../api/consultation'
import { APPOINTMENT_STATUS, VISIT_TYPE } from '../../constants/appointments'
import { ageGroup, formatSlot, genderLabel } from '../../utils/format'
import TopBar from '../../components/layout/TopBar'
import VideoPlaceholder from '../../components/appointment/VideoPlaceholder'
import PrescriptionItems from '../../components/appointment/PrescriptionItems'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Pill from '../../components/ui/Pill'
import { ErrorState, LoadingState } from '../../components/ui/States'

// 의사 예약 상세 (J-2) · 진료 시작 (J-3) · 진료 중 화면 (J-6)
export default function DoctorAppointmentPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const detail = useQuery({ queryKey: ['doctor-appointment', id], queryFn: () => getDoctorAppointment(id) })
  const start = useMutation({
    mutationFn: () => startConsultation(id),
    onSuccess: (data) => {
      queryClient.setQueryData(['doctor-appointment', id], data)
      queryClient.invalidateQueries({ queryKey: ['schedule'] })
    },
  })

  const title = detail.data?.status === 'in_progress' ? '진료 중' : '예약 상세'
  if (detail.isPending) return <><TopBar title={title} /><LoadingState /></>
  if (detail.isError) return <><TopBar title={title} /><ErrorState message={detail.error.message} /></>

  const a = detail.data
  const status = APPOINTMENT_STATUS[a.status]
  const meta = [ageGroup(a.subject_birth_year), genderLabel(a.subject_gender)].filter(Boolean).join(' ')

  return (
    <div className="flex flex-1 flex-col">
      <TopBar title={title} />
      <div className="flex flex-col gap-3 p-5">
        {a.status === 'in_progress' && (
          <>
            <div className="flex items-center justify-between gap-3 rounded-[18px] bg-doctor px-[18px] py-4 text-white">
              <span className="flex flex-col gap-0.5">
                <span className="text-[17px] font-bold">{a.subject_name} 님 진료 중</span>
                <span className="text-[13px]">{formatSlot(a.started_at)} 시작 · 환자 화면에도 진료 중으로 보여요</span>
              </span>
            </div>
            <VideoPlaceholder description="진료를 마치면 아래에서 완료 처리해주세요" />
          </>
        )}

        <Card>
          <div className="flex items-center gap-3">
            <span className="flex size-12 shrink-0 items-center justify-center rounded-full bg-surface text-lg font-bold text-ink-muted">
              {a.subject_name.slice(0, 1)}
            </span>
            <div className="flex flex-col gap-1">
              <p className="text-[17px] font-bold">{[a.subject_name, meta].filter(Boolean).join(' · ')}</p>
              <span className="flex gap-1.5">
                <Pill tone={a.visit_type === 'first' ? 'wait' : 'muted'}>{VISIT_TYPE[a.visit_type]}</Pill>
                <Pill tone={a.status === 'booked' ? 'doctor' : status.tone}>{status.label}</Pill>
              </span>
            </div>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-ink-muted">진료 시간</span>
            <span className="font-medium">{formatSlot(a.start_at)}</span>
          </div>
          {a.status === 'cancelled' && <p className="text-sm text-ink-muted">취소 사유: {a.cancel_reason}</p>}
        </Card>

        <Card>
          <h2 className="text-[15px] font-bold">증상 메모</h2>
          <p className="text-sm whitespace-pre-line">{a.symptom_note || '남긴 메모가 없어요'}</p>
        </Card>

        {a.status === 'completed' && (
          <Card>
            <h2 className="text-[15px] font-bold">진료 요약</h2>
            <p className="text-sm whitespace-pre-line">{a.doctor_summary}</p>
            {a.prescription ? (
              <>
                <h2 className="mt-1 text-[15px] font-bold">처방전 {a.prescription.code}</h2>
                <PrescriptionItems prescription={a.prescription} />
              </>
            ) : (
              <p className="text-[13px] text-ink-muted">처방 없이 진료를 마쳤어요</p>
            )}
          </Card>
        )}

        <Card>
          <h2 className="text-[15px] font-bold">이전 진료 기록</h2>
          {a.history.length === 0 ? (
            <p className="rounded-xl bg-surface px-4 py-3.5 text-sm text-ink-muted">이 환자와의 이전 진료가 없어요</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {a.history.map((h) => (
                <li key={h.id} className="rounded-xl bg-surface px-4 py-3 text-sm">
                  <p className="text-xs text-ink-muted">{formatSlot(h.start_at)}</p>
                  <p className="line-clamp-3">{h.doctor_summary}</p>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      {(a.status === 'booked' || a.status === 'in_progress') && (
        <div className="sticky bottom-0 mt-auto flex flex-col gap-2 border-t border-line bg-white px-5 pt-3 pb-6">
          {start.isError && <p role="alert" className="text-[13px] text-wait">{start.error.message}</p>}
          {a.status === 'booked' ? (
            <Button variant="doctor" className="w-full" disabled={start.isPending} onClick={() => start.mutate()}>
              {start.isPending ? '시작하는 중…' : '진료 시작하기'}
            </Button>
          ) : (
            <Button variant="doctor" className="w-full" onClick={() => navigate(`/doctor/appointments/${a.id}/complete`)}>
              진료 완료하기
            </Button>
          )}
        </div>
      )}
    </div>
  )
}
