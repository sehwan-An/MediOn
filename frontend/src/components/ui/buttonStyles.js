// 피그마 Button 컴포넌트 (높이 52px). <Link> 를 버튼처럼 보일 때도 이 클래스를 쓴다.
const VARIANTS = {
  primary: 'bg-primary text-white',
  doctor: 'bg-doctor text-white',
  secondary: 'border border-line bg-white text-ink',
  soft: 'bg-primary-soft text-primary',
}

export function buttonClass(variant = 'primary', className = '') {
  const base =
    'inline-flex h-13 items-center justify-center gap-2 rounded-[14px] px-5 text-base font-bold transition-opacity hover:opacity-90 disabled:opacity-50'
  return `${base} ${VARIANTS[variant] ?? VARIANTS.primary} ${className}`.trim()
}
