"""질문·답변 (B, C, D, F-3).

공개 범위: 공개 질문은 누구나, 비공개 질문은 작성자와 인증된 의사만 본다. 볼 수 없으면 404.
"""

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import (
    Answer, AnswerRecommendedDepartment, Department, DoctorProfile, HelpfulVote, Question, User,
)
from app.schemas.appointment import DoctorBrief
from app.schemas.question import (
    AnswerIn, AnswerOut, DoctorAnswerItem, MyQuestions, QuestionBrief, QuestionDetail, QuestionIn, StatusCounts,
)
from app.services.notification_service import notify

LIST_LIMIT = 50  # shortcut: 목록은 최근 50개까지. 질문이 많아지면 페이지네이션


def _is_verified_doctor(user: User | None) -> bool:
    return bool(user and user.role == "doctor" and user.doctor_profile and user.doctor_profile.is_verified)


def _visible(db: Session, user: User | None, question_id: int) -> Question:
    q = db.get(Question, question_id)
    if q is None:
        raise AppError(404, "NOT_FOUND", "질문을 찾을 수 없어요")
    if q.visibility == "private" and not (user and user.id == q.author_id) and not _is_verified_doctor(user):
        raise AppError(404, "NOT_FOUND", "질문을 찾을 수 없어요")
    return q


def _check_department(db: Session, code: str | None) -> None:
    if code is not None and db.get(Department, code) is None:
        raise AppError(400, "VALIDATION_ERROR", "진료 분야를 다시 선택해주세요")


def create(db: Session, patient: User, data: QuestionIn) -> QuestionDetail:
    """질문 작성 (B-1, B-2)."""
    _check_department(db, data.department_code)
    q = Question(author_id=patient.id, **data.model_dump(), status="waiting", answer_count=0)
    db.add(q)
    db.commit()
    return detail(db, patient, q.id)


def feed(db: Session, department: str | None, keyword: str | None) -> list[QuestionBrief]:
    """상담 피드 (C-1~C-3): 답변이 달린 공개 질문, 최신순."""
    query = select(Question).where(Question.visibility == "public", Question.status == "answered")
    if department:
        query = query.where(Question.department_code == department)
    if keyword and keyword.strip():
        k = keyword.strip()
        query = query.where(or_(Question.title.contains(k, autoescape=True), Question.body.contains(k, autoescape=True)))
    return [QuestionBrief.model_validate(q) for q in db.scalars(query.order_by(Question.id.desc()).limit(LIST_LIMIT))]


def detail(db: Session, user: User | None, question_id: int) -> QuestionDetail:
    """질문 상세 (C-4): 질문 요약 + 의사 답변 카드."""
    q = _visible(db, user, question_id)
    author = db.get(User, q.author_id)
    answers = list(db.scalars(select(Answer).where(Answer.question_id == q.id).order_by(Answer.id)))
    ids = [a.id for a in answers]
    profiles = {p.user_id: p for p in db.scalars(select(DoctorProfile).where(
        DoctorProfile.user_id.in_([a.doctor_id for a in answers])))} if answers else {}
    depts: dict[int, list[str]] = {}
    for r in db.scalars(select(AnswerRecommendedDepartment).where(AnswerRecommendedDepartment.answer_id.in_(ids))) if ids else []:
        depts.setdefault(r.answer_id, []).append(r.department_code)
    helped = set(db.scalars(select(HelpfulVote.answer_id).where(
        HelpfulVote.user_id == user.id, HelpfulVote.answer_id.in_(ids)))) if user and ids else set()
    out = []
    for a in answers:
        p = profiles[a.doctor_id]
        out.append(AnswerOut(
            id=a.id, doctor=DoctorBrief(id=p.user_id, name=p.name, department_code=p.department_code, hospital_name=p.hospital_name),
            body=a.body, recommends_visit=a.recommends_visit, recommended_departments=sorted(depts.get(a.id, [])),
            helpful_count=a.helpful_count, helped=a.id in helped, created_at=a.created_at,
        ))
    return QuestionDetail(
        **QuestionBrief.model_validate(q).model_dump(), body_part=q.body_part, duration=q.duration,
        author_birth_year=author.birth_year if author else None, author_gender=author.gender if author else None,
        is_mine=bool(user and user.id == q.author_id),
        answered_by_me=bool(user and any(a.doctor_id == user.id for a in answers)), answers=out,
    )


def remove(db: Session, patient: User, question_id: int) -> None:
    """질문 삭제 (B-6). 작성자만, 답변이 있어도 삭제할 수 있다."""
    q = db.get(Question, question_id)
    if q is None or q.author_id != patient.id:
        raise AppError(404, "NOT_FOUND", "질문을 찾을 수 없어요")
    db.delete(q)
    db.commit()


def mine(db: Session, patient: User, status: str | None) -> MyQuestions:
    """내 질문 (B-5): 상태별 개수 + 목록."""
    rows = dict(db.execute(select(Question.status, func.count()).where(Question.author_id == patient.id)
                           .group_by(Question.status)).all())
    counts = StatusCounts(all=sum(rows.values()), waiting=rows.get("waiting", 0), answered=rows.get("answered", 0))
    query = select(Question).where(Question.author_id == patient.id)
    if status:
        query = query.where(Question.status == status)
    items = [QuestionBrief.model_validate(q) for q in db.scalars(query.order_by(Question.id.desc()).limit(LIST_LIMIT))]
    return MyQuestions(counts=counts, items=items)


def inbox(db: Session, doctor: User, mine_only: bool) -> list[QuestionBrief]:
    """의사 답변 대기 목록 (D-1, D-2): 답변 없는 질문, 오래 기다린 순."""
    query = select(Question).where(Question.status == "waiting")
    if mine_only:
        query = query.where(Question.department_code == doctor.doctor_profile.department_code)
    return [QuestionBrief.model_validate(q) for q in db.scalars(query.order_by(Question.id).limit(LIST_LIMIT))]


def answer(db: Session, doctor: User, question_id: int, data: AnswerIn) -> QuestionDetail:
    """답변 작성 (D-3, D-4) = 답변 + 추천 진료과 + 질문 상태 + 답변 수 + 환자 알림(F-3)을 한 트랜잭션으로."""
    q = _visible(db, doctor, question_id)
    codes = sorted(set(data.recommended_departments)) if data.recommends_visit else []
    if data.recommends_visit and not codes:
        raise AppError(400, "VALIDATION_ERROR", "대면 진료를 권할 진료과를 골라주세요")
    for code in codes:
        _check_department(db, code)

    a = Answer(question_id=q.id, doctor_id=doctor.id, body=data.body, recommends_visit=data.recommends_visit)
    db.add(a)
    try:
        db.flush()  # 같은 의사가 두 번 답변하면 (question_id, doctor_id) 유니크 위반
    except IntegrityError as exc:
        db.rollback()
        raise AppError(409, "ALREADY_ANSWERED", "이미 답변한 질문이에요") from exc
    db.add_all(AnswerRecommendedDepartment(answer_id=a.id, department_code=c) for c in codes)
    # 답변 수는 DB 에서 더한다 (동시에 답변해도 숫자가 맞게)
    db.execute(update(Question).where(Question.id == q.id)
               .values(status="answered", answer_count=Question.answer_count + 1))
    notify(db, q.author_id, "answer_arrived", f"{doctor.doctor_profile.name} 의사가 '{q.title}'에 답변했어요",
           question_id=q.id)
    db.commit()
    db.refresh(q)
    return detail(db, doctor, q.id)


def toggle_helpful(db: Session, user: User, answer_id: int) -> tuple[int, bool]:
    """도움돼요 (C-5). 답변마다 1번, 다시 누르면 취소."""
    a = db.get(Answer, answer_id)
    if a is None:
        raise AppError(404, "NOT_FOUND", "답변을 찾을 수 없어요")
    _visible(db, user, a.question_id)
    removed = db.execute(delete(HelpfulVote).where(HelpfulVote.user_id == user.id, HelpfulVote.answer_id == a.id)).rowcount
    if removed:
        db.execute(update(Answer).where(Answer.id == a.id).values(helpful_count=Answer.helpful_count - 1))
    else:
        db.add(HelpfulVote(user_id=user.id, answer_id=a.id))
        db.execute(update(Answer).where(Answer.id == a.id).values(helpful_count=Answer.helpful_count + 1))
    try:
        db.commit()
    except IntegrityError:  # 거의 동시에 두 번 누름: 이미 눌린 상태로 본다
        db.rollback()
    db.refresh(a)
    helped = db.scalar(select(HelpfulVote.answer_id).where(HelpfulVote.user_id == user.id, HelpfulVote.answer_id == a.id))
    return a.helpful_count, helped is not None


def my_answers(db: Session, doctor: User) -> list[DoctorAnswerItem]:
    """내 답변 목록 (D-6)."""
    rows = db.execute(select(Answer, Question.title).join(Question, Question.id == Answer.question_id)
                      .where(Answer.doctor_id == doctor.id).order_by(Answer.id.desc()).limit(LIST_LIMIT))
    return [DoctorAnswerItem(answer_id=a.id, question_id=a.question_id, question_title=title,
                             helpful_count=a.helpful_count, created_at=a.created_at) for a, title in rows]
