"""근처 약국 조회 (M-1, tech-spec 8). 공공데이터포털 '국립중앙의료원 전국 약국 정보 조회 서비스'.

키가 없거나 호출이 실패하면 샘플 약국 목록을 돌려줘서 화면 개발·시연을 막지 않는다.
요청 파라미터·응답 필드는 공공데이터포털 문서 기준으로 PC 에서 키를 넣고 한 번 확인할 것.
"""

import math
import time

import httpx
import xmltodict

from app.core.config import settings

URL = "https://apis.data.go.kr/B552657/ErmctInsttInfoInqireService/getParmacyLcinfoInqire"
TIMEOUT_SECONDS = 5
CACHE_SECONDS = 24 * 60 * 60

# shortcut: 서버 메모리 캐시라 서버를 다시 켜면 비워진다. 서버를 여러 대 띄우면 pharmacies_cache 테이블로 옮길 것
_cache: dict[str, tuple[float, list[dict]]] = {}

# 키가 없을 때 쓰는 가상 약국 (기준 위치 근처에 흩어 놓는다). 이름은 모두 가상
SAMPLE = [("봄빛약국", 0.0021, 0.0018), ("새솔약국", -0.0032, 0.0041), ("푸른잎약국", 0.0049, -0.0035),
          ("햇살온약국", -0.0058, -0.0022), ("다온약국", 0.0071, 0.0063)]


def _distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> int:
    dy = (lat2 - lat1) * 111_000
    dx = (lng2 - lng1) * 111_000 * math.cos(math.radians(lat1))
    return round(math.hypot(dx, dy))


def _sample(lat: float, lng: float) -> list[dict]:
    rows = [{
        "ext_id": f"SAMPLE{i}", "name": name, "address": "광주광역시 서구 (데모 주소)", "tel": None,
        "lat": round(lat + dlat, 6), "lng": round(lng + dlng, 6), "open_hours": "09:00~21:00",
    } for i, (name, dlat, dlng) in enumerate(SAMPLE, 1)]
    return _with_distance(rows, lat, lng, sample=True)


def _with_distance(rows: list[dict], lat: float, lng: float, sample: bool = False) -> list[dict]:
    for r in rows:
        r["distance_m"] = _distance_m(lat, lng, r["lat"], r["lng"])
        r["is_sample"] = sample
    return sorted(rows, key=lambda r: r["distance_m"])  # 거리순만. 특정 약국을 앞에 두지 않는다 (알선 금지)


def _hhmm(value) -> str | None:
    value = str(value or "")
    return f"{value[:2]}:{value[2:4]}" if len(value) >= 4 else None


def _fetch(lat: float, lng: float) -> list[dict]:
    res = httpx.get(URL, params={
        "serviceKey": settings.data_go_kr_service_key, "WGS84_LON": lng, "WGS84_LAT": lat, "pageNo": 1, "numOfRows": 20,
    }, timeout=TIMEOUT_SECONDS)
    res.raise_for_status()
    items = (xmltodict.parse(res.text).get("response", {}).get("body", {}).get("items") or {}).get("item") or []
    if isinstance(items, dict):  # 결과가 1개면 리스트가 아니라 dict 로 온다
        items = [items]
    rows = []
    for it in items:
        try:
            start, end = _hhmm(it.get("startTime")), _hhmm(it.get("endTime"))
            rows.append({
                "ext_id": str(it["hpid"])[:20], "name": it["dutyName"], "address": it.get("dutyAddr") or "",
                "tel": it.get("dutyTel1"), "lat": float(it["latitude"]), "lng": float(it["longitude"]),
                "open_hours": f"{start}~{end}" if start and end else None,
            })
        except (KeyError, TypeError, ValueError):
            continue  # 필드가 빠진 약국은 건너뛴다
    return _with_distance(rows, lat, lng)


def nearby(lat: float, lng: float) -> list[dict]:
    """좌표 근처 약국, 거리순. 좌표를 소수 둘째 자리(약 1km)로 묶어서 24시간 캐시한다."""
    key = f"{lat:.2f}:{lng:.2f}"
    cached = _cache.get(key)
    if cached and time.time() - cached[0] < CACHE_SECONDS:
        return _with_distance([dict(r) for r in cached[1]], lat, lng, cached[1][0]["is_sample"] if cached[1] else False)
    if not settings.data_go_kr_service_key:
        return _sample(lat, lng)
    try:
        rows = _fetch(lat, lng)
    except (httpx.HTTPError, ValueError, AttributeError):
        rows = []
    if not rows:  # 실패하거나 결과가 없으면 오래된 캐시 → 샘플 순서로 대신한다
        return cached[1] if cached else _sample(lat, lng)
    _cache[key] = (time.time(), rows)
    return rows
