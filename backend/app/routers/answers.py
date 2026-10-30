"""답변 API (D, C-5). 답변은 인증 승인된 의사만.

- D-1, D-2  GET  /doctor/qna?mine_only=true      답변 대기 질문, 오래 기다린 순
- D-3, D-4  POST /questions/{id}/answers         답변 작성 (+ 환자 알림, 한 트랜잭션)
- D-6       GET  /doctor/answers                 내 답변 목록
- C-5       POST /answers/{id}/helpful           도움돼요 토글 (환자)
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role, require_verified_doctor
from app.models import User
from app.schemas.question import AnswerIn, DoctorAnswerItem, HelpfulOut, QuestionBrief, QuestionDetail
from app.services import question_service

router = APIRouter(tags=["answers"])


@router.get("/doctor/qna", response_model=list[QuestionBrief])
def inbox(mine_only: bool = False, doctor: User = Depends(require_verified_doctor), db: Session = Depends(get_db)):
    return question_service.inbox(db, doctor, mine_only)


@router.post("/questions/{question_id}/answers", response_model=QuestionDetail, status_code=status.HTTP_201_CREATED)
def answer(question_id: int, body: AnswerIn, doctor: User = Depends(require_verified_doctor), db: Session = Depends(get_db)):
    return question_service.answer(db, doctor, question_id, body)


@router.get("/doctor/answers", response_model=list[DoctorAnswerItem])
def my_answers(doctor: User = Depends(require_verified_doctor), db: Session = Depends(get_db)):
    return question_service.my_answers(db, doctor)


@router.post("/answers/{answer_id}/helpful", response_model=HelpfulOut)
def helpful(answer_id: int, user: User = Depends(require_role("patient")), db: Session = Depends(get_db)):
    count, helped = question_service.toggle_helpful(db, user, answer_id)
    return HelpfulOut(helpful_count=count, helped=helped)
