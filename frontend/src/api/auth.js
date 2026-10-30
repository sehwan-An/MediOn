import client from './client'

// 무료 서버가 잠들어 있으면 첫 응답까지 오래 걸려서 타임아웃을 길게 둔다 (A-0)
export const getHealth = () => client.get('/health', { timeout: 60000 }).then((r) => r.data)

export const login = (payload) => client.post('/auth/login', payload).then((r) => r.data)
export const signup = (payload) => client.post('/auth/signup', payload).then((r) => r.data)
// formData: 의사 정보 + 인증 서류 파일 (A-9)
export const signupDoctor = (formData) => client.post('/auth/signup/doctor', formData).then((r) => r.data)

export const getMe = () => client.get('/auth/me').then((r) => r.data)
export const updateMe = (payload) => client.patch('/auth/me', payload).then((r) => r.data)
export const getMySummary = () => client.get('/me/summary').then((r) => r.data)
