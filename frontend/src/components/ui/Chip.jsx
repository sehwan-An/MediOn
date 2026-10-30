// 진료 분야 필터·선택. tone: patient | doctor (피그마 Chip 컴포넌트)
export default function Chip({ selected = false, tone = 'patient', className = '', children, ...props }) {
  let look = 'border border-line bg-white font-medium text-ink'
  if (selected) {
    look = tone === 'doctor'
      ? 'border border-doctor bg-doctor-soft font-bold text-doctor'
      : 'border border-primary bg-primary font-bold text-white'
  }
  return (
    <button
      type="button"
      aria-pressed={selected}
      className={`inline-flex h-9 shrink-0 items-center justify-center rounded-full px-3.5 text-sm ${look} ${className}`.trim()}
      {...props}
    >
      {children}
    </button>
  )
}
