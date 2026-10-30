"""건강보험심사평가원 병원정보서비스 호출 (tech-spec 8).

외부 API 는 이 파일에서만 호출한다.

TODO (E-1, E-2)
- httpx 로 호출, 타임아웃 5초 (인증키: settings.data_go_kr_service_key)
- XML 응답을 xmltodict 로 변환 후 필요한 필드만 남기기
  { name, address, tel, lat, lng, distance_m }
- hospitals_cache 테이블로 24시간 캐시, 실패 시 오래된 캐시라도 반환 / 없으면 503
- 정확한 요청 파라미터는 공공데이터포털 API 문서로 확인
"""

TIMEOUT_SECONDS = 5
CACHE_HOURS = 24


def make_cache_key(department_code: str, lat: float, lng: float) -> str:
    """좌표는 소수 둘째 자리로 반올림해서 비슷한 위치끼리 캐시를 공유한다."""
    return f"dept:{department_code}:lat:{lat:.2f}:lng:{lng:.2f}"
