"""근처 병원 API (tech-spec 8. 외부 API 연동)

TODO
- E-1, E-2  GET /hospitals   ?department=05&lat=&lng=&radius=  (services/hira_client.py 사용)
"""

from fastapi import APIRouter

router = APIRouter(prefix="/hospitals", tags=["hospitals"])
