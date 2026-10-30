// 화면 표시용 변환. 서버는 UTC 로 주고, 한국 시간 표시는 화면에서 한다 (tech-spec 4)

// 출생연도 → "30대" (의사에게는 나이대까지만 보여준다)
export function ageGroup(birthYear, now = new Date()) {
  if (!birthYear) return null
  const age = now.getFullYear() - birthYear
  if (age < 10) return '10대 미만'
  return `${Math.floor(age / 10) * 10}대`
}

export function genderLabel(gender) {
  return { M: '남성', F: '여성' }[gender] ?? null
}

// "2026.10.30 09:20" (한국 시간)
export function formatDateTime(iso) {
  if (!iso) return ''
  const parts = new Intl.DateTimeFormat('ko-KR', {
    timeZone: 'Asia/Seoul',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).formatToParts(new Date(iso))
  const get = (type) => parts.find((p) => p.type === type)?.value ?? ''
  return `${get('year')}.${get('month')}.${get('day')} ${get('hour')}:${get('minute')}`
}

// 로그인 뒤 돌아갈 주소. 외부 주소로 튕기는 것을 막기 위해 앱 안의 경로만 허용한다
export function safeReturnPath(from) {
  return typeof from === 'string' && from.startsWith('/') && !from.startsWith('//') ? from : null
}

// ---- 예약 날짜·시간 (한국 시간). 한국은 서머타임이 없어서 UTC+9 를 더해 getUTC* 로 읽는다
const KST_OFFSET_MS = 9 * 60 * 60 * 1000
const DAY_MS = 24 * 60 * 60 * 1000
const WEEKDAYS = ['일', '월', '화', '수', '목', '금', '토']
// 서버 진료 시간표는 0=월 … 6=일
export const SCHEDULE_WEEKDAYS = ['월', '화', '수', '목', '금', '토', '일']

const toKst = (value) => new Date(new Date(value).getTime() + KST_OFFSET_MS)
const kstKey = (kst) => kst.toISOString().slice(0, 10)
const pad = (n) => String(n).padStart(2, '0')

// 오늘부터 count 일 (예약 날짜 선택용). scheduleWeekday 는 서버 요일 번호(0=월)
export function upcomingDays(count = 7, now = new Date()) {
  const today = toKst(now)
  return Array.from({ length: count }, (_, i) => {
    const d = new Date(today.getTime() + i * DAY_MS)
    return {
      key: kstKey(d),
      month: d.getUTCMonth() + 1,
      day: d.getUTCDate(),
      weekday: i === 0 ? '오늘' : WEEKDAYS[d.getUTCDay()],
      scheduleWeekday: (d.getUTCDay() + 6) % 7,
    }
  })
}

// "오늘 14:30", "내일 10:00", "11.2 (월) 10:00"
export function formatSlot(iso, now = new Date()) {
  const k = toKst(iso)
  const diff = Math.round((Date.parse(kstKey(k)) - Date.parse(kstKey(toKst(now)))) / DAY_MS)
  let day = `${k.getUTCMonth() + 1}.${k.getUTCDate()} (${WEEKDAYS[k.getUTCDay()]})`
  if (diff === 0) day = '오늘'
  if (diff === 1) day = '내일'
  return `${day} ${pad(k.getUTCHours())}:${pad(k.getUTCMinutes())}`
}

// "09:00:00" → "09:00"
export const hhmm = (time) => time?.slice(0, 5) ?? ''

// 서버 요일 번호(0=월)로 오늘 진료 시간 찾기
export function todayHours(schedules, now = new Date()) {
  const weekday = (toKst(now).getUTCDay() + 6) % 7
  const s = schedules.find((x) => x.weekday === weekday)
  return s ? `${hhmm(s.start_time)}~${hhmm(s.end_time)}` : '휴진'
}
