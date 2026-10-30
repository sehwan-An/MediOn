import { buttonClass } from './buttonStyles'

// variant: primary(환자) | doctor(의사) | secondary(보조) | soft(약한 강조)
export default function Button({ variant = 'primary', type = 'button', className = '', children, ...props }) {
  return (
    <button type={type} className={buttonClass(variant, className)} {...props}>
      {children}
    </button>
  )
}
