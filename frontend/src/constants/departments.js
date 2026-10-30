// 진료과 목록. 백엔드 departments 테이블(scripts/seed.py)과 코드를 똑같이 맞춘다.
// 코드는 심평원 진료과목 코드 기준이며, 공공데이터포털 문서로 최종 확인할 것.
export const DEPARTMENTS = [
  { code: '05', name: '정형외과' },
  { code: '01', name: '내과' },
  { code: '12', name: '안과' },
  { code: '14', name: '피부과' },
  { code: '13', name: '이비인후과' },
  { code: '11', name: '소아청소년과' },
  { code: '03', name: '정신건강의학과' },
  { code: '21', name: '재활의학과' },
  { code: '23', name: '가정의학과' },
]

export const departmentName = (code) => DEPARTMENTS.find((d) => d.code === code)?.name ?? '잘 모르겠어요'
