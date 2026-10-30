import Icon from './Icon'
import Button from './Button'

// 모든 데이터 화면은 로딩 / 에러 / 빈 상태를 처리한다 (CLAUDE.md)

export function LoadingState({ message = '불러오는 중이에요' }) {
  return (
    <div role="status" className="flex flex-1 flex-col items-center justify-center gap-3 py-16 text-ink-muted">
      <Icon name="loader" size={28} className="animate-spin" />
      <p className="text-sm">{message}</p>
    </div>
  )
}

export function ErrorState({ message = '문제가 생겼어요. 잠시 후 다시 시도해주세요', onRetry }) {
  return (
    <div role="alert" className="flex flex-1 flex-col items-center justify-center gap-4 px-6 py-16 text-center">
      <Icon name="alert" size={32} className="text-wait" />
      <p className="text-[15px] text-ink">{message}</p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          다시 시도
        </Button>
      )}
    </div>
  )
}

export function EmptyState({ title, description, action }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-2 px-6 py-16 text-center">
      <p className="text-[17px] font-bold text-ink">{title}</p>
      {description && <p className="text-sm text-ink-muted">{description}</p>}
      {action && <div className="mt-3">{action}</div>}
    </div>
  )
}
