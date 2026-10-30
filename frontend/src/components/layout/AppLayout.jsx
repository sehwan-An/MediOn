import { Outlet } from 'react-router-dom'
import DemoBanner from './DemoBanner'
import LoginSheet from './LoginSheet'

// 휴대폰에서는 화면을 꽉 채우고, 넓은 화면(md 이상)에서는 390×844 휴대폰 크기 프레임 안에 보여준다.
// 프레임(바깥)은 고정, 안쪽 영역만 스크롤된다. 그래서 상단 배너·하단 탭은 sticky 로 붙어 있고,
// 바텀시트는 스크롤과 상관없이 프레임 전체를 덮을 수 있다.
export default function AppLayout() {
  return (
    <div className="min-h-dvh md:flex md:items-center md:justify-center md:bg-line md:p-6">
      <div
        id="app-frame"
        className="relative flex min-h-dvh w-full flex-col bg-surface md:h-[min(844px,calc(100dvh-3rem))] md:min-h-0 md:w-[390px] md:overflow-hidden md:rounded-[36px] md:border-[6px] md:border-ink md:shadow-2xl"
      >
        <div className="flex flex-1 flex-col md:min-h-0 md:overflow-y-auto">
          <DemoBanner />
          <Outlet />
        </div>
        <LoginSheet />
      </div>
    </div>
  )
}
