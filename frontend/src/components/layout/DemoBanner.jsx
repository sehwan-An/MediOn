import Icon from '../ui/Icon'

// 모든 화면 최상단 고정 (A-4). 지우지 않는다.
export default function DemoBanner() {
  return (
    <div
      role="note"
      className="sticky top-0 z-30 flex items-center justify-center gap-1.5 bg-ink px-4 py-1.5 text-xs font-medium text-white"
    >
      <Icon name="info" size={14} />
      포트폴리오용 데모 · 실제 의료 서비스가 아니에요
    </div>
  )
}
