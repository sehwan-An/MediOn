import { Link } from 'react-router-dom'
import { buttonClass } from '../components/ui/buttonStyles'
import { EmptyState } from '../components/ui/States'

export default function NotFoundPage() {
  return (
    <EmptyState
      title="페이지를 찾을 수 없어요"
      description="주소가 바뀌었거나 삭제된 페이지예요"
      action={
        <Link to="/" className={buttonClass('primary')}>
          홈으로
        </Link>
      }
    />
  )
}
