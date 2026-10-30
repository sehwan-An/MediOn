// 역할별 첫 화면
export function isVerifiedDoctor(user) {
  return user?.role === 'doctor' && user?.doctor_profile?.verification_status === 'approved'
}

export function homePathFor(user) {
  if (!user) return '/'
  if (user.role === 'admin') return '/admin/doctors'
  if (user.role === 'doctor') return isVerifiedDoctor(user) ? '/doctor' : '/doctor/pending'
  return '/'
}
