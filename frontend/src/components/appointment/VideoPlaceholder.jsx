import Icon from '../ui/Icon'

// 화상통화 자리 표시 (J-6). 화상통화는 보류라서 진료는 의사가 상태만 바꾼다 (idea.md 12)
export default function VideoPlaceholder({ description }) {
  return (
    <div className="flex h-52 flex-col items-center justify-center gap-2.5 rounded-[18px] bg-ink px-6 text-center text-white">
      <span className="flex size-13 items-center justify-center rounded-full bg-white text-ink">
        <Icon name="video" size={26} />
      </span>
      <p className="text-base font-bold">화상통화는 준비 중이에요</p>
      <p className="text-[13px]">{description}</p>
    </div>
  )
}
