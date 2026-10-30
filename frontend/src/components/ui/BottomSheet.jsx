import { useEffect, useRef } from 'react'

// 바텀시트 (로그인 안내, 예약 취소 등). 휴대폰에서는 화면 전체, 넓은 화면에서는 휴대폰 프레임(#app-frame) 안을 덮는다.
// 열릴 때 시트 안의 첫 버튼에 포커스, Esc·바깥 클릭으로 닫힌다.
export default function BottomSheet({ open, onClose, titleId, children }) {
  const sheetRef = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    sheetRef.current?.querySelector('button')?.focus()
    const onKeyDown = (event) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-40 flex flex-col justify-end md:absolute">
      <button type="button" aria-label="닫기" tabIndex={-1} onClick={onClose} className="absolute inset-0 bg-ink/50" />
      <div
        ref={sheetRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="relative flex flex-col gap-2.5 rounded-t-3xl bg-white px-5 pt-3 pb-[calc(1.75rem+env(safe-area-inset-bottom))]"
      >
        <span aria-hidden="true" className="mx-auto h-1 w-10 rounded-full bg-line" />
        {children}
      </div>
    </div>
  )
}
