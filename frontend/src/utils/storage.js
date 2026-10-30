// localStorage 는 시크릿 모드 등에서 막힐 수 있어서 항상 try/catch 로 감싼다
export const TOKEN_KEY = 'medion:token'
export const STARTED_KEY = 'medion:started'

export const storage = {
  get(key) {
    try {
      return window.localStorage.getItem(key)
    } catch {
      return null
    }
  },
  set(key, value) {
    try {
      window.localStorage.setItem(key, value)
    } catch {
      // 저장소를 쓸 수 없으면 이번 세션 동안만 메모리 상태로 동작
    }
  },
  remove(key) {
    try {
      window.localStorage.removeItem(key)
    } catch {
      // 무시
    }
  },
}
