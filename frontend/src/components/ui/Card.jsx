// 흰색 카드 (피그마 화면의 기본 카드: 모서리 18px, 안쪽 여백 18px)
export default function Card({ as: Tag = 'section', className = '', children, ...props }) {
  return (
    <Tag className={`flex flex-col gap-3 rounded-[18px] bg-white p-[18px] ${className}`.trim()} {...props}>
      {children}
    </Tag>
  )
}
