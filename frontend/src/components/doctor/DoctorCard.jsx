import { Link } from 'react-router-dom'
import { departmentName } from '../../constants/departments'
import { formatSlot } from '../../utils/format'
import Icon from '../ui/Icon'
import Pill from '../ui/Pill'

// 의사 목록 카드 (H-2, 피그마 Doctor Card)
export default function DoctorCard({ doctor }) {
  return (
    <Link to={`/doctors/${doctor.id}`} className="flex flex-col gap-3.5 rounded-[18px] bg-white p-[18px]">
      <div className="flex items-center gap-3">
        <span className="flex size-12 shrink-0 items-center justify-center rounded-full bg-doctor-soft text-lg font-bold text-doctor">
          {doctor.name.slice(0, 1)}
        </span>
        <span className="flex min-w-0 flex-1 flex-col gap-0.5">
          <span className="truncate text-xs text-ink-muted">{doctor.hospital_name}</span>
          <span className="flex items-center gap-1.5">
            <span className="text-base font-bold">{doctor.name} 의사</span>
            <Icon name="verified" size={16} className="text-primary" />
            <Pill>{departmentName(doctor.department_code)}</Pill>
          </span>
        </span>
        <Icon name="chevronRight" size={20} className="text-ink-muted" />
      </div>
      <div className="flex items-center justify-between gap-2 rounded-xl bg-surface px-3 py-2.5 text-[13px]">
        <span className="font-medium text-ink-muted">
          {doctor.review_count > 0 ? `재진 희망 ${doctor.revisit_rate}% (후기 ${doctor.review_count})` : '아직 후기가 없어요'}
        </span>
        <span className={`font-bold ${doctor.next_available_at ? 'text-primary' : 'text-ink-muted'}`}>
          {doctor.next_available_at ? `${formatSlot(doctor.next_available_at)} 예약 가능` : '7일 안에 빈 시간 없음'}
        </span>
      </div>
    </Link>
  )
}
