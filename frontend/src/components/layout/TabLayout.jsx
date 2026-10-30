import { Outlet } from 'react-router-dom'
import BottomNav from './BottomNav'

// 하단 탭이 있는 화면 (환자: 홈/진료 내역/마이, 의사: 진료 일정/마이)
// 하단 탭은 sticky 라서 내용이 짧아도 프레임 맨 아래에 붙는다 (main 이 남는 높이를 채움)
export default function TabLayout({ role }) {
  return (
    <>
      <main className="flex flex-1 flex-col">
        <Outlet />
      </main>
      <BottomNav role={role} />
    </>
  )
}
