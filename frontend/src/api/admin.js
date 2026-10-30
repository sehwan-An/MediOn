import client from './client'

// 의사 인증 심사 (A-11). 관리자만
export const getDoctorApplications = (params) => client.get('/admin/doctors', { params }).then((r) => r.data)
// 서류 파일은 공개 주소가 없어서 로그인 토큰으로 받아온다 (Blob)
export const getDoctorDocument = (doctorId, docId) =>
  client.get(`/admin/doctors/${doctorId}/documents/${docId}`, { responseType: 'blob' }).then((r) => r.data)
// payload: { action: 'approve' | 'reject', reason }
export const reviewDoctor = (doctorId, payload) => client.patch(`/admin/doctors/${doctorId}`, payload).then((r) => r.data)
