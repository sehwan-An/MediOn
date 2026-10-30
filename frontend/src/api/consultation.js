import client from './client'

// 의사 진료 콘솔 (J-1~J-4, L-1). 인증 승인된 의사만
export const getSchedule = (date) => client.get('/doctor/appointments', { params: { date } }).then((r) => r.data)
export const getDoctorAppointment = (id) => client.get(`/doctor/appointments/${id}`).then((r) => r.data)
export const startConsultation = (id) => client.post(`/doctor/appointments/${id}/start`).then((r) => r.data)
export const completeConsultation = (id, payload) =>
  client.post(`/doctor/appointments/${id}/complete`, payload).then((r) => r.data)
export const searchDrugs = (q) => client.get('/drugs', { params: { q } }).then((r) => r.data)
