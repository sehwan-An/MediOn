import client from './client'

// 질문 (B, C). 피드·상세는 로그인 없이도 볼 수 있다
export const getQuestions = (params) => client.get('/questions', { params }).then((r) => r.data)
export const getQuestion = (id) => client.get(`/questions/${id}`).then((r) => r.data)
export const createQuestion = (payload) => client.post('/questions', payload).then((r) => r.data)
export const deleteQuestion = (id) => client.delete(`/questions/${id}`)
export const getMyQuestions = (params) => client.get('/me/questions', { params }).then((r) => r.data)
