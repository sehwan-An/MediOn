import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getAppointment } from '../../api/appointments'
import { getPrescription } from '../../api/payments'
import { VISIT_TYPE } from '../../constants/appointments'
import { departmentName } from '../../constants/departments'
import { formatDateTime } from '../../utils/format'
import TopBar from '../../components/layout/TopBar'
import PrescriptionItems from '../../components/appointment/PrescriptionItems'
import { buttonClass } from '../../components/ui/buttonStyles'
import Icon from '../../components/ui/Icon'
import Pill from '../../components/ui/Pill'
import { ErrorState, LoadingState } from '../../components/ui/States'

// 처방전 보기 (L-3). 결제 후에만 열리고, 항상 "데모 처방전" 워터마크를 표시한다 (CLAUDE.md)
export default function PrescriptionPage() {
  const { id } = useParams()
  const rx = useQuery({ queryKey: ['prescription', id], queryFn: () => getPrescription(id), retry: false })
  const appointment = useQuery({ queryKey: ['appointment', id], queryFn: () => getAppointment(id) })

  if (rx.isPending) return <><TopBar title="처방전" /><LoadingState /></>
  if (rx.isError) {
    return (
      <>
        <TopBar title="처방전" />
        <ErrorState message={rx.error.message} />
        {rx.error.code === 'PAYMENT_REQUIRED' && (
          <div className="px-5"><Link to={`/appointments/${id}/pay`} className={buttonClass('primary', 'w-full')}>결제하러 가기</Link></div>
        )}
      </>
    )
  }

  const p = rx.data
  const sent = Boolean(appointment.data?.pharmacy_order)

  return (
    <div className="flex flex-1 flex-col">
      <TopBar title="처방전" />
      <div className="flex flex-col gap-3 p-5">
        <section className="relative flex flex-col gap-3 overflow-hidden rounded-[18px] bg-white p-[18px]">
          <span aria-hidden="true" className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 rotate-[-24deg] text-5xl font-bold whitespace-nowrap text-primary opacity-[0.07]">
            DEMO 처방전
          </span>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-xl font-bold">처방전</h1>
              <p className="text-[13px] font-medium text-ink-muted">{p.code}</p>
            </div>
            <Pill tone="wait">데모 처방전</Pill>
          </div>
          <dl className="flex flex-col border-y border-line py-2 text-sm">
            {[
              ['발급일', formatDateTime(p.issued_at)],
              ['환자', `${p.patient_name} · ${p.patient_birth_year}년생`],
              ['의사', `${p.doctor_name} · ${departmentName(p.department_code)}`],
              ['의료기관', p.hospital_name],
              ['진료 구분', VISIT_TYPE[p.visit_type]],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between py-1.5">
                <dt className="text-ink-muted">{label}</dt>
                <dd className="font-medium">{value}</dd>
              </div>
            ))}
          </dl>
          <h2 className="text-[15px] font-bold">처방 의약품 {p.items.length}개</h2>
          <PrescriptionItems prescription={p} />
        </section>
        <p className="flex gap-2 rounded-xl bg-wait-soft px-3.5 py-3 text-[13px] font-medium text-wait">
          <Icon name="info" size={18} className="shrink-0" />
          포트폴리오용 데모 처방전이에요. 실제 약국에서 사용할 수 없어요.
        </p>
      </div>
      <div className="sticky bottom-0 mt-auto border-t border-line bg-white px-5 pt-3 pb-6">
        <Link to={sent ? `/appointments/${id}` : `/appointments/${id}/pharmacy`} className={buttonClass('primary', 'w-full')}>
          {sent ? '약 수령 상태 보기' : '약국 선택하기'}
        </Link>
      </div>
    </div>
  )
}
