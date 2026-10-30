import client from './client'

// 예약 (I-2, I-7~I-9). 로그인한 환자만
export const bookAppointment = (payload) => client.post('/appointments', payload).then((r) => r.data)
export const getAppointments = (tab) => client.get('/appointments', { params: { tab } }).then((r) => r.data)
export const getAppointment = (id) => client.get(`/appointments/${id}`).then((r) => r.data)
export const cancelAppointment = (id, reason) => client.post(`/appointments/${id}/cancel`, { reason }).then((r) => r.data)
// 후기 (N-1): { wants_revisit, tags: ['kind' | 'detailed' | 'punctual'], body }
export const createReview = (id, payload) => client.post(`/appointments/${id}/review`, payload).then((r) => r.data)
