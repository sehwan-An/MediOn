"""2차 테스트: 질문·답변 (B-1, B-2, B-5, B-6, C-1~C-5, D-1~D-4, D-6, F-3)."""

import pytest

from app.core.security import create_access_token
from app.models import Department, DoctorProfile, User
from tests.test_appointments import signup

QUESTION = {"department_code": "01", "title": "기침이 오래가요", "body": "2주째 마른기침이 나요", "duration": "1-2w"}


@pytest.fixture
def doctors(session_factory):
    """인증 의사(내과) 2명 + 심사 중 의사 1명의 토큰 헤더."""
    headers = {}
    with session_factory() as db:
        db.add_all([Department(code="01", name="내과", sort_order=0), Department(code="13", name="이비인후과", sort_order=1)])
        for key, dept, status in [("a", "01", "approved"), ("b", "13", "approved"), ("pending", "01", "pending")]:
            u = User(email=f"{key}@doc.com", password_hash="x", nickname=key, role="doctor")
            db.add(u)
            db.flush()
            db.add(DoctorProfile(user_id=u.id, name=f"의사{key}", department_code=dept, hospital_name="가상의원",
                                 license_number="1", verification_status=status))
            headers[key] = {"Authorization": "Bearer " + create_access_token(u.id, "doctor")}
        db.commit()
    return headers


def ask(client, headers, **extra):
    return client.post("/api/questions", headers=headers, json={**QUESTION, **extra})


def test_create_validation(client, doctors):
    patient = signup(client, "p@x.com")
    assert ask(client, patient, title="  ").json()["error"]["message"] == "제목을 입력해주세요"
    assert ask(client, patient, body="가" * 1001).json()["error"]["message"] == "1,000자까지 입력할 수 있어요"
    assert ask(client, patient, department_code="99").status_code == 400
    assert ask(client, doctors["a"]).status_code == 403  # 의사는 질문 못 함
    res = ask(client, patient, department_code=None)
    assert res.status_code == 201 and res.json()["status"] == "waiting" and res.json()["is_mine"] is True


def test_answer_flow_feed_and_notification(client, doctors):
    patient = signup(client, "p@x.com")
    qid = ask(client, patient).json()["id"]
    assert client.get("/api/questions").json() == []  # 답변 전에는 피드에 없음

    # 대기 목록 (D-1, D-2): 내 진료과만 켜면 이비인후과 의사에게는 안 보임
    assert [q["id"] for q in client.get("/api/doctor/qna", headers=doctors["b"]).json()] == [qid]
    assert client.get("/api/doctor/qna", headers=doctors["b"], params={"mine_only": True}).json() == []
    assert client.get("/api/doctor/qna", headers=doctors["pending"]).status_code == 403

    url = f"/api/questions/{qid}/answers"
    bad = client.post(url, headers=doctors["a"], json={"body": "답변", "recommends_visit": True})
    assert bad.status_code == 400  # 대면 진료 권유면 진료과 필수
    res = client.post(url, headers=doctors["a"], json={"body": "물을 자주 드세요", "recommends_visit": True,
                                                       "recommended_departments": ["13", "01"]})
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "answered" and body["answer_count"] == 1 and body["answered_by_me"] is True
    assert body["answers"][0]["recommended_departments"] == ["01", "13"]
    assert client.post(url, headers=doctors["a"], json={"body": "또"}).json()["error"]["code"] == "ALREADY_ANSWERED"
    client.post(url, headers=doctors["b"], json={"body": "가습기를 써보세요"})

    feed = client.get("/api/questions").json()
    assert [q["id"] for q in feed] == [qid] and feed[0]["answer_count"] == 2
    assert client.get("/api/questions", params={"q": "마른기침"}).json()[0]["id"] == qid  # C-3
    assert client.get("/api/questions", params={"q": "두통"}).json() == []
    assert client.get("/api/questions", params={"department": "13"}).json() == []  # C-2

    notes = client.get("/api/notifications", headers=patient).json()
    assert notes[0]["type"] == "answer_arrived" and notes[0]["question_id"] == qid

    mine = client.get("/api/me/questions", headers=patient).json()
    assert mine["counts"] == {"all": 1, "waiting": 0, "answered": 1}
    assert len(client.get("/api/doctor/answers", headers=doctors["a"]).json()) == 1


def test_private_question_is_hidden(client, doctors):
    patient = signup(client, "p@x.com")
    qid = ask(client, patient, visibility="private").json()["id"]
    client.post(f"/api/questions/{qid}/answers", headers=doctors["a"], json={"body": "답변"})
    assert client.get("/api/questions").json() == []  # 비공개는 피드에 없음
    assert client.get(f"/api/questions/{qid}").status_code == 404  # 게스트
    assert client.get(f"/api/questions/{qid}", headers=signup(client, "s@x.com")).status_code == 404  # 다른 환자
    assert client.get(f"/api/questions/{qid}", headers=patient).status_code == 200
    assert client.get(f"/api/questions/{qid}", headers=doctors["b"]).status_code == 200


def test_helpful_toggle_and_delete(client, doctors):
    patient = signup(client, "p@x.com")
    qid = ask(client, patient).json()["id"]
    answer_id = client.post(f"/api/questions/{qid}/answers", headers=doctors["a"], json={"body": "답변"}).json()["answers"][0]["id"]
    other = signup(client, "o@x.com")
    url = f"/api/answers/{answer_id}/helpful"
    assert client.post(url, headers=other).json() == {"helpful_count": 1, "helped": True}
    assert client.post(url, headers=patient).json() == {"helpful_count": 2, "helped": True}
    assert client.post(url, headers=other).json() == {"helpful_count": 1, "helped": False}  # 다시 누르면 취소
    assert client.get(f"/api/questions/{qid}", headers=patient).json()["answers"][0]["helped"] is True

    assert client.delete(f"/api/questions/{qid}", headers=other).status_code == 404  # 남의 질문
    assert client.delete(f"/api/questions/{qid}", headers=patient).status_code == 204
    assert client.get(f"/api/questions/{qid}").status_code == 404
