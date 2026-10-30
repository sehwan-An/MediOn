import { useId } from 'react'

// 라벨 + 입력창 + 안내/에러 문구. 에러는 빨강 대신 wait 색으로 보여준다 (CLAUDE.md 색 규칙)
// trailing: 입력창 오른쪽에 붙는 버튼 (예: 비밀번호 보기)
export default function TextField({ label, optional = false, hint, error, trailing = null, ...inputProps }) {
  const id = useId()
  const messageId = `${id}-message`
  const message = error || hint

  return (
    <div className="flex flex-col gap-2">
      {label && (
        <label htmlFor={id} className="flex items-center gap-1 text-sm font-bold text-ink">
          {label}
          {optional && <span className="font-normal text-ink-muted">선택</span>}
        </label>
      )}
      <div className="relative">
        <input
          id={id}
          aria-invalid={Boolean(error)}
          aria-describedby={message ? messageId : undefined}
          className={`h-13 w-full rounded-[14px] border bg-white px-4 text-[15px] text-ink outline-none placeholder:text-ink-muted focus:border-primary ${
            error ? 'border-wait' : 'border-line'
          } ${trailing ? 'pr-12' : ''}`}
          {...inputProps}
        />
        {trailing && <div className="absolute inset-y-0 right-1 flex items-center">{trailing}</div>}
      </div>
      {message && (
        <p id={messageId} className={`text-[13px] ${error ? 'text-wait' : 'text-ink-muted'}`}>
          {message}
        </p>
      )}
    </div>
  )
}
