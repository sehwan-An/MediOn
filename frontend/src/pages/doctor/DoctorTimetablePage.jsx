import { useQuery } from '@tanstack/react-query'
import { getDoctor } from '../../api/doctors'
import useAuth from '../../context/useAuth'
import TopBar from '../../components/layout/TopBar'
import ScheduleList from '../../components/doctor/ScheduleList'
import Card from '../../components/ui/Card'
import Icon from '../../components/ui/Icon'
import { ErrorState, LoadingState } from '../../components/ui/States'

// 의사 진료 시간표 (I-1). 1차는 시드 데이터로 넣고 보기만 한다. 공개 의사 상세 API 를 그대로 쓴다
export default function DoctorTimetablePage() {
  const { user } = useAuth()
  const doctor = useQuery({ queryKey: ['doctor', String(user.id)], queryFn: () => getDoctor(user.id) })

  return (
    <div className="flex flex-1 flex-col">
      <TopBar title="진료 시간표" />
      <div className="flex flex-col gap-3 p-5">
        <p className="flex gap-2 rounded-xl bg-primary-soft px-3.5 py-3 text-[13px] font-medium text-primary">
          <Icon name="info" size={18} className="shrink-0" />
          1차에서는 시드 데이터로 넣은 시간표를 보기만 해요. 예약은 30분 단위로, 오늘부터 7일까지 열려요.
        </p>
        {doctor.isPending && <LoadingState />}
        {doctor.isError && <ErrorState message={doctor.error.message} onRetry={doctor.refetch} />}
        {doctor.isSuccess && (
          <Card className="gap-1">
            <ScheduleList schedules={doctor.data.schedules} />
          </Card>
        )}
      </div>
    </div>
  )
}
