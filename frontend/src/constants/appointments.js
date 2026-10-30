// 예약 상태 표시 (requirements 2. 예약 상태). 빨강·초록 대신 파랑(예약·완료)·회색(취소)
export const APPOINTMENT_STATUS = {
  booked: { label: '예약됨', tone: 'done' },
  in_progress: { label: '진료 중', tone: 'primary' },
  completed: { label: '진료 완료', tone: 'done' },
  cancelled: { label: '취소됨', tone: 'muted' },
}

export const VISIT_TYPE = { first: '초진', return: '재진' }

export const CANCEL_REASONS = ['일정이 바뀌었어요', '증상이 나아졌어요', '다른 의사에게 진료받을래요', '기타']

// 약 수령 상태 (M-4)
export const PHARMACY_STATUS = {
  sent: '처방전 전송됨',
  preparing: '조제 중',
  ready: '수령 대기',
  shipping: '배송 중',
  received: '수령 완료',
}
export const PHARMACY_FLOW = {
  pickup: ['sent', 'preparing', 'ready', 'received'],
  delivery: ['sent', 'preparing', 'shipping', 'received'],
}

// 약 배송 대상 (M-2). 제도 초기 합의 기준, 확정되면 다시 확인 (idea.md 7)
export const DELIVERY_REASONS = [
  { value: 'remote_area', label: '섬·벽지 거주', description: '의료기관 접근이 어려운 지역' },
  { value: 'long_term_care', label: '장기요양 수급자', description: '장기요양 등급을 받은 분' },
  { value: 'disability', label: '장애인', description: '등록 장애인' },
  { value: 'rare_disease', label: '희귀질환자', description: '희귀질환 산정특례 대상' },
]

export const won = (n) => `${n.toLocaleString('ko-KR')}원`

// 후기 태그 (N-1). 백엔드 schemas/review.py 의 Tag 와 같게
export const REVIEW_TAGS = [
  { value: 'kind', label: '친절한 진료' },
  { value: 'detailed', label: '자세한 설명' },
  { value: 'punctual', label: '예약 시간 준수' },
]
