import client from './client'

// 오늘 복용표 (P-1, P-2). 환자만
export const getTodayMedications = () => client.get('/me/medications/today').then((r) => r.data)
// payload: { prescription_id, slot, taken } → 바뀐 오늘 복용표
export const checkMedication = (payload) => client.post('/me/medications/check', payload).then((r) => r.data)
