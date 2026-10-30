import client from './client'

// 결제 (K) · 처방전 (L-3) · 약국 (M). 로그인한 환자만
export const getPayment = (appointmentId) => client.get(`/appointments/${appointmentId}/payment`).then((r) => r.data)
export const demoPay = (appointmentId) => client.post(`/appointments/${appointmentId}/payment/demo`).then((r) => r.data)
export const confirmPayment = (payload) => client.post('/payments/confirm', payload).then((r) => r.data)
export const failPayment = (payload) => client.post('/payments/fail', payload).then((r) => r.data)
export const getMyPayments = () => client.get('/me/payments').then((r) => r.data)
export const getPrescription = (appointmentId) => client.get(`/appointments/${appointmentId}/prescription`).then((r) => r.data)
export const getPharmacies = (lat, lng) => client.get('/pharmacies', { params: { lat, lng } }).then((r) => r.data)
export const sendToPharmacy = (appointmentId, payload) =>
  client.post(`/appointments/${appointmentId}/pharmacy-order`, payload).then((r) => r.data)
export const advancePharmacyOrder = (appointmentId) =>
  client.post(`/appointments/${appointmentId}/pharmacy-order/advance`).then((r) => r.data)
