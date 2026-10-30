import { Link } from 'react-router-dom'
import Icon from './Icon'

// 마이 화면의 메뉴 한 줄. to 가 있으면 링크, 없으면 onClick 버튼
export default function MenuItem({ icon, label, description, to, onClick, muted = false }) {
  const content = (
    <>
      <Icon name={icon} size={22} className={muted ? 'text-ink-muted' : 'text-ink'} />
      <span className="flex flex-1 flex-col text-left">
        <span className={`text-[15px] font-medium ${muted ? 'text-ink-muted' : 'text-ink'}`}>{label}</span>
        {description && <span className="text-xs text-ink-muted">{description}</span>}
      </span>
      <Icon name="chevronRight" size={18} className="text-ink-muted" />
    </>
  )
  const className = 'flex min-h-14 w-full items-center gap-3 px-[18px] py-3'

  if (to) {
    return (
      <Link to={to} className={className}>
        {content}
      </Link>
    )
  }
  return (
    <button type="button" onClick={onClick} className={className}>
      {content}
    </button>
  )
}
