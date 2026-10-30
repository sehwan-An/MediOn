import client from './client'

// 의사 찾기 (H-1, H-2, H-5, H-6). 로그인 없이 쓸 수 있다
export const getCategories = () => client.get('/categories').then((r) => r.data)
export const getDoctors = (params) => client.get('/doctors', { params }).then((r) => r.data)
export const getDoctor = (id) => client.get(`/doctors/${id}`).then((r) => r.data)
export const getSlots = (id, date) => client.get(`/doctors/${id}/slots`, { params: { date } }).then((r) => r.data)
// 후기 (N-2): 재진 희망률, 태그별 인원, 후기 목록
export const getDoctorReviews = (id) => client.get(`/doctors/${id}/reviews`).then((r) => r.data)
