import axios from 'axios'
import { storage, TOKEN_KEY } from '../utils/storage'

export const LOGOUT_EVENT = 'medion:logout'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api',
  timeout: 15000,
})

client.interceptors.request.use((config) => {
  const token = storage.get(TOKEN_KEY)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 백엔드 에러 형식 { error: { code, message } } 을 Error 로 바꿔서 화면에서 message 를 그대로 보여준다
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const body = error.response?.data?.error
    let message = body?.message
    if (!message) {
      message = error.code === 'ECONNABORTED'
        ? '서버 응답이 늦어요. 잠시 후 다시 시도해주세요'
        : '문제가 생겼어요. 잠시 후 다시 시도해주세요'
    }
    if (status === 401 && storage.get(TOKEN_KEY)) {
      window.dispatchEvent(new Event(LOGOUT_EVENT))
    }
    return Promise.reject(Object.assign(new Error(message), { status, code: body?.code }))
  },
)

export default client
