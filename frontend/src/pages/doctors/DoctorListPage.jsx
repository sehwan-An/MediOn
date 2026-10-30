import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getCategories, getDoctors } from '../../api/doctors'
import { departmentName } from '../../constants/departments'
import TopBar from '../../components/layout/TopBar'
import DoctorCard from '../../components/doctor/DoctorCard'
import Chip from '../../components/ui/Chip'
import { EmptyState, ErrorState, LoadingState } from '../../components/ui/States'

// 의사 목록 (H-2). ?category=cold 로 들어오고, 진료과 칩으로 더 좁힌다 (?department=01)
// "오늘 진료 가능" 필터·정렬(H-3)은 아직 없다
export default function DoctorListPage() {
  const [params, setParams] = useSearchParams()
  const category = params.get('category')
  const department = params.get('department')

  const categories = useQuery({ queryKey: ['categories'], queryFn: getCategories, staleTime: Infinity })
  const current = categories.data?.find((c) => c.code === category)
  const doctors = useQuery({
    queryKey: ['doctors', category, department],
    queryFn: () => getDoctors({ category: category ?? undefined, department: department ?? undefined }),
  })

  const pickDepartment = (code) => {
    const next = new URLSearchParams(params)
    if (code) next.set('department', code)
    else next.delete('department')
    setParams(next, { replace: true })
  }

  return (
    <div className="flex flex-1 flex-col">
      <TopBar title={current?.name ?? '의사 찾기'} />
      {current && current.departments.length > 1 && (
        <div className="flex gap-2 overflow-x-auto bg-white px-5 pt-1 pb-3.5">
          <Chip selected={!department} onClick={() => pickDepartment(null)}>
            전체
          </Chip>
          {current.departments.map((code) => (
            <Chip key={code} selected={department === code} onClick={() => pickDepartment(code)}>
              {departmentName(code)}
            </Chip>
          ))}
        </div>
      )}
      <div className="flex flex-1 flex-col gap-3 p-5">
        {doctors.isPending && <LoadingState />}
        {doctors.isError && <ErrorState message={doctors.error.message} onRetry={doctors.refetch} />}
        {doctors.isSuccess && doctors.data.length === 0 && (
          <EmptyState title="아직 이 진료과 의사가 없어요" description="다른 진료과를 골라보세요" />
        )}
        {doctors.isSuccess && doctors.data.length > 0 && (
          <>
            <p className="text-[13px] font-medium text-ink-muted">의사 {doctors.data.length}명 · 빨리 예약할 수 있는 순</p>
            {doctors.data.map((d) => (
              <DoctorCard key={d.id} doctor={d} />
            ))}
          </>
        )}
      </div>
    </div>
  )
}
