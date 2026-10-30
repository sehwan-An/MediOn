import client from './client'

// 답변 (D) · 도움돼요 (C-5)
export const createAnswer = (questionId, payload) =>
  client.post(`/questions/${questionId}/answers`, payload).then((r) => r.data)
export const toggleHelpful = (answerId) => client.post(`/answers/${answerId}/helpful`).then((r) => r.data)

// 의사 전용
export const getDoctorInbox = (params) => client.get('/doctor/qna', { params }).then((r) => r.data)
export const getDoctorAnswers = () => client.get('/doctor/answers').then((r) => r.data)
