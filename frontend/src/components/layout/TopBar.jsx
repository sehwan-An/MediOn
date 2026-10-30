import { Link, useNavigate } from 'react-router-dom'
import Icon from '../ui/Icon'

// 하위 화면 상단 바: 뒤로 가기(44px) + 제목 + 오른쪽 슬롯 (기본은 홈 버튼. 의사·관리자는 / 에서 각자 첫 화면으로 이동)
export default function TopBar({ title, right }) {
  const navigate = useNavigate()
  return (
    <header className="sticky top-7 z-20 flex h-14 items-center justify-between border-b border-line bg-white px-2">
      <button type="button" aria-label="뒤로 가기" onClick={() => navigate(-1)} className="flex size-11 items-center justify-center">
        <Icon name="chevronLeft" size={24} />
      </button>
      <h1 className="text-[17px] font-bold">{title}</h1>
      <div className="flex min-w-11 items-center justify-end">
        {right === undefined ? (
          <Link to="/" aria-label="홈으로" className="flex size-11 items-center justify-center">
            <Icon name="home" size={22} />
          </Link>
        ) : right}
      </div>
    </header>
  )
}
