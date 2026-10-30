import TopBar from './TopBar'
import PageHeader from './PageHeader'

// 아직 구현하지 않은 화면. 기능 ID 는 docs/requirements.md 참고
// header: 'tab'(큰 제목 + 알림) | 'back'(뒤로 가기) | 'plain'(제목만)
export default function PagePlaceholder({ title, ids = [], header = 'plain', step, children = null }) {
  let top = (
    <header className="bg-white px-5 py-4">
      <h1 className="text-[22px] font-bold">{title}</h1>
    </header>
  )
  if (header === 'tab') top = <PageHeader title={title} />
  if (header === 'back') top = <TopBar title={title} />

  return (
    <div className="flex flex-1 flex-col">
      {top}
      <div className="flex flex-1 flex-col items-center justify-center gap-2 px-6 py-16 text-center">
        <p className="text-[17px] font-bold">준비 중인 화면이에요</p>
        {ids.length > 0 && <p className="text-sm text-ink-muted">기능 {ids.join(', ')}</p>}
        {step && <p className="text-sm text-ink-muted">{step}단계에서 만들어요</p>}
        {children && <div className="mt-4 w-full">{children}</div>}
      </div>
    </div>
  )
}
