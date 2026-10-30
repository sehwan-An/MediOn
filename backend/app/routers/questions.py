"""질문 API (B, C). 피드·상세는 로그인 없이도 볼 수 있다 (비공개 질문은 작성자·의사만, 아니면 404).

- C-1~C-3  GET    /questions?department=&q=   상담 피드: 답변 달린 공개 질문, 최신순
- C-4      GET    /questions/{id}             상세 + 답변 카드
- B-1      POST   /questions                  질문 작성 (환자)
- B-6      DELETE /questions/{id}             삭제 (작성자)
- B-5      GET    /me/questions?status=       내 질문 + 상태별 개수

TODO
- B-6  PATCH /questions/{id} 수정, B-3 사진 첨부, B-4 임시저장
"""

from typing import Literal

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_optional_user, require_role
from app.models import User
from app.schemas.question import MyQuestions, QuestionBrief, QuestionDetail, QuestionIn
from app.services import question_service

router = APIRouter(tags=["questions"])
patient_only = require_role("patient")


@router.get("/questions", response_model=list[QuestionBrief])
def feed(department: str | None = None, q: str | None = None, db: Session = Depends(get_db)):
    return question_service.feed(db, department, q)


@router.get("/questions/{question_id}", response_model=QuestionDetail)
def detail(question_id: int, user: User | None = Depends(get_optional_user), db: Session = Depends(get_db)):
    return question_service.detail(db, user, question_id)


@router.post("/questions", response_model=QuestionDetail, status_code=status.HTTP_201_CREATED)
def create(body: QuestionIn, user: User = Depends(patient_only), db: Session = Depends(get_db)):
    return question_service.create(db, user, body)


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove(question_id: int, user: User = Depends(patient_only), db: Session = Depends(get_db)) -> None:
    question_service.remove(db, user, question_id)


@router.get("/me/questions", response_model=MyQuestions)
def mine(status: Literal["waiting", "answered"] | None = None, user: User = Depends(patient_only),
         db: Session = Depends(get_db)):
    return question_service.mine(db, user, status)
