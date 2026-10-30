// 질문·답변 (B, C, D). 백엔드 schemas/question.py 와 같게

export const DURATIONS = [
  { value: 'today', label: '오늘부터' },
  { value: '1-2w', label: '1~2주' },
  { value: '1m', label: '한 달쯤' },
  { value: 'longer', label: '그보다 오래' },
]
export const durationLabel = (value) => DURATIONS.find((d) => d.value === value)?.label ?? value

export const QUESTION_STATUS = {
  waiting: { label: '답변 대기', tone: 'wait' },
  answered: { label: '답변 도착', tone: 'done' },
}

export const TITLE_MAX = 100
export const BODY_MAX = 1000

// 답변 기다린 시간: "3시간째", "2일째"
export function waitedFor(iso, now = new Date()) {
  const minutes = Math.max(0, Math.floor((now - new Date(iso)) / 60000))
  if (minutes < 60) return `${minutes}분째`
  if (minutes < 60 * 24) return `${Math.floor(minutes / 60)}시간째`
  return `${Math.floor(minutes / 60 / 24)}일째`
}
