"""시드 데이터 입력 (requirements.md 5. 데모 시드 데이터)

실행: python -m scripts.seed          진료과·시연용 계정 등 기본 데이터 입력 (여러 번 실행해도 중복으로 안 들어감)
      python -m scripts.seed --reset  시연용 계정이 만든 데이터까지 초기화 (A-5)

시연용 계정의 이메일·비밀번호는 README 의 "시연용 계정" 표와 같게 유지한다.
모든 이름·병원은 가상이다.
"""

import argparse
from datetime import UTC, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.fees import fee_for
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import (
    Answer, AnswerRecommendedDepartment, Appointment, Department, DoctorDocument, DoctorProfile, DoctorSchedule, Drug,
    Payment, PharmacyOrder, Prescription, PrescriptionItem, Question, Review, User,
)
from app.services import storage
from app.services.payment_service import _new_order_id
from app.services.slot_service import KST

# 진료과 코드는 심평원 진료과목 코드와 같게 맞춘다. 공공데이터포털 문서로 최종 확인할 것.
DEPARTMENTS = [
    ("05", "정형외과"),
    ("01", "내과"),
    ("12", "안과"),
    ("14", "피부과"),
    ("13", "이비인후과"),
    ("11", "소아청소년과"),
    ("03", "정신건강의학과"),
    ("21", "재활의학과"),
    ("23", "가정의학과"),
]

DEMO_PASSWORD = "medion1234"

# (이메일, 닉네임, 역할, 출생연도, 성별)
DEMO_USERS = [
    ("jiwoo@demo.medion", "한지우", "patient", 1994, "F"),   # 페르소나 A: 30대 직장인
    ("minjae@demo.medion", "최민재", "patient", 1992, "M"),  # 페르소나 B: 부모님 대신 예약하는 보호자
    ("admin@demo.medion", "관리자", "admin", None, None),
]

# (이메일, 이름, 진료과 코드, 병원, 인증 상태, 소개, 진료 시간표 이름)
DEMO_DOCTORS = [
    ("doyoon@demo.medion", "김도윤", "01", "가온내과의원", "approved", "감기, 소화기 질환, 만성질환 관리를 주로 진료해요.", "standard"),
    ("seojin@demo.medion", "박서진", "13", "맑은숨이비인후과의원", "approved", "비염, 목감기, 귀 질환을 주로 진료해요.", "standard"),
    ("haram@demo.medion", "정하람", "23", "하람가정의원", "approved", "가족 모두의 일상 건강을 함께 살펴요.", "late"),
    ("chaewon@demo.medion", "윤채원", "01", "새봄내과의원", "approved", "당뇨·고혈압 같은 만성질환 관리를 도와드려요.", "alternate"),
    ("jian@demo.medion", "서지안", "14", "고운결피부과의원", "approved", "여드름, 피부염, 탈모 상담을 주로 해요.", "standard"),
    ("maru@demo.medion", "한마루", "05", "튼튼정형외과의원", "approved", "허리·무릎·어깨 통증을 주로 진료해요.", "standard"),
    ("serin@demo.medion", "오세린", "11", "아이숲소아청소년과의원", "approved", "아이들의 감기, 열, 성장 상담을 해요.", "late"),
    ("iden@demo.medion", "강이든", "03", "마음쉼정신건강의학과의원", "approved", "불면, 우울, 불안으로 힘든 마음을 함께 살펴요.", "alternate"),
    ("bom@demo.medion", "문가람", "12", "밝은눈안과의원", "approved", "안구건조증, 결막염 등 눈 불편함을 진료해요.", "standard"),
    ("hajun@demo.medion", "임하준", "21", "바른재활의학과의원", "approved", "통증 관리와 재활 운동을 안내해드려요.", "alternate"),
    ("hyunwoo@demo.medion", "이현우", "05", "바른정형외과의원", "pending", None, None),
]

# 진료 시간표 (I-1). (요일 0=월…6=일, 시작, 끝, 점심 시작, 점심 끝), 한국 시간
WEEKDAYS_9_TO_6 = [(d, "09:00", "18:00", "13:00", "14:00") for d in range(5)]
SCHEDULES = {
    "standard": WEEKDAYS_9_TO_6 + [(5, "09:00", "13:00", None, None)],
    "late": [(d, "10:00", "20:00", "13:00", "14:00") for d in range(5)] + [(5, "09:00", "14:00", None, None)],
    "alternate": [(d, "09:00", "18:00", "12:30", "13:30") for d in (0, 2, 4)] + [(5, "09:00", "13:00", None, None)],
}


# 처방전 작성용 데모 약 (L-1). 실제 제품이 아닌 가상의 이름·제조사다 (CLAUDE.md 의료 데모 데이터 원칙)
DEMO_DRUGS = [(f"데모{name}", maker, form) for name, maker, form in [
    ("해열정 500mg", "데모제약", "정"), ("해열시럽", "데모제약", "시럽"), ("감기캡슐", "가상약품", "캡슐"),
    ("기침시럽", "가상약품", "시럽"), ("가래정", "데모제약", "정"), ("코막힘정", "온누리가상제약", "정"),
    ("비염캡슐", "온누리가상제약", "캡슐"), ("항히스타민정", "가상약품", "정"), ("인후스프레이", "데모제약", "스프레이"),
    ("위장정", "데모제약", "정"), ("소화캡슐", "가상약품", "캡슐"), ("제산현탁액", "온누리가상제약", "현탁액"),
    ("정장정", "데모제약", "정"), ("진경정", "가상약품", "정"), ("구역정", "온누리가상제약", "정"),
    ("소염진통정", "데모제약", "정"), ("근이완정", "가상약품", "정"), ("파스", "온누리가상제약", "패치"),
    ("관절겔", "데모제약", "겔"), ("피부연고", "데모제약", "연고"), ("보습크림", "가상약품", "크림"),
    ("여드름겔", "온누리가상제약", "겔"), ("가려움정", "데모제약", "정"), ("두피액", "가상약품", "외용액"),
    ("인공눈물", "데모제약", "점안액"), ("결막염점안액", "가상약품", "점안액"), ("소아해열시럽", "온누리가상제약", "시럽"),
    ("소아정장산", "데모제약", "산제"), ("수면보조정", "가상약품", "정"), ("안정정", "온누리가상제약", "정"),
]]


# 지난 진료 (requirements 5): 완료·결제·후기까지 끝난 기록. 재진 희망률·진료 내역 표시용
# (환자, 의사, 며칠 전, 재진 희망, 태그, 후기 내용)
PAST_VISITS = [
    ("jiwoo@demo.medion", "doyoon@demo.medion", 40, True, ["kind", "detailed"], "설명을 차근차근 해주셔서 좋았어요."),
    ("jiwoo@demo.medion", "doyoon@demo.medion", 21, True, ["detailed", "punctual"], None),
    ("jiwoo@demo.medion", "seojin@demo.medion", 33, True, ["kind"], "출근 전에 짧게 상담받을 수 있어서 편했어요."),
    ("jiwoo@demo.medion", "jian@demo.medion", 15, False, ["punctual"], None),
    ("jiwoo@demo.medion", "bom@demo.medion", 8, True, ["kind", "punctual"], "예약 시간에 맞춰 바로 시작했어요."),
    ("minjae@demo.medion", "haram@demo.medion", 45, True, ["kind", "detailed", "punctual"], "부모님 대신 예약했는데 친절하게 안내해주셨어요."),
    ("minjae@demo.medion", "chaewon@demo.medion", 30, True, ["detailed"], "생활 습관 관리 방법을 자세히 알려주셨어요."),
    ("minjae@demo.medion", "maru@demo.medion", 26, False, [], "대면 진료를 권해주셨어요."),
    ("minjae@demo.medion", "serin@demo.medion", 18, True, ["kind"], None),
    ("minjae@demo.medion", "hajun@demo.medion", 12, True, ["detailed", "punctual"], "집에서 할 수 있는 운동을 알려주셨어요."),
    ("minjae@demo.medion", "doyoon@demo.medion", 6, False, ["punctual"], None),
    ("jiwoo@demo.medion", "iden@demo.medion", 3, True, ["kind", "detailed"], "편하게 이야기할 수 있었어요."),
]
PAST_SUMMARY = "비대면으로 증상을 확인했어요. 증상이 계속되거나 심해지면 가까운 병원에서 대면 진료를 받아보세요."

# 심사 중 의사(이현우)의 데모 서류. 실제 면허증이 아닌 안내 문구만 있는 PDF
DEMO_LICENSE_PDF = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 420 300]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 120>>stream
BT /F1 18 Tf 40 200 Td (MediON DEMO DOCUMENT) Tj 0 -40 Td /F1 12 Tf (Sample license - fictional, not a real document) Tj ET
endstream endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
trailer<</Root 1 0 R>>
%%EOF
"""


def seed_doctor_documents(db: Session) -> int:
    """서류가 없는 시연용 심사 중 의사에게 데모 면허증을 넣는다 (관리자 심사 화면 시연용)."""
    added = 0
    for email, *_, status, _bio, _plan in DEMO_DOCTORS:
        doctor_id = db.scalar(select(User.id).where(User.email == email))
        if status != "pending" or doctor_id is None:
            continue
        if db.scalar(select(DoctorDocument.id).where(DoctorDocument.doctor_id == doctor_id)) is None:
            db.add(DoctorDocument(doctor_id=doctor_id, type="license", file_key=storage.save(DEMO_LICENSE_PDF, "pdf")))
            added += 1
    return added


def seed_past_visits(db: Session) -> int:
    """지난 진료 + 데모 결제 + 후기. 이미 넣었으면(같은 진료 요약 문구가 있으면) 건너뛴다."""
    if db.scalar(select(Appointment.id).where(Appointment.doctor_summary == PAST_SUMMARY).limit(1)):
        return 0
    ids = dict(db.execute(select(User.email, User.id)).all())
    today = datetime.now(KST).replace(hour=10, minute=0, second=0, microsecond=0)
    seen: set[tuple[str, str]] = set()
    for patient_email, doctor_email, days_ago, revisit, tags, body in PAST_VISITS:
        patient = db.get(User, ids[patient_email])
        doctor_id = ids[doctor_email]
        start = (today - timedelta(days=days_ago)).astimezone(UTC)
        visit_type = "return" if (patient_email, doctor_email) in seen else "first"
        seen.add((patient_email, doctor_email))
        a = Appointment(
            patient_id=patient.id, doctor_id=doctor_id, subject_name=patient.nickname,
            subject_birth_year=patient.birth_year, subject_gender=patient.gender,
            start_at=start, end_at=start + timedelta(minutes=30), slot_key=start, status="completed",
            visit_type=visit_type, doctor_summary=PAST_SUMMARY, started_at=start, completed_at=start + timedelta(minutes=15),
        )
        db.add(a)
        db.flush()
        _, amount = fee_for(start.astimezone(KST).year - patient.birth_year, visit_type)
        doctor_name = db.get(DoctorProfile, doctor_id).name
        db.add(Payment(appointment_id=a.id, patient_id=patient.id, order_id=_new_order_id(a.id),
                       order_name=f"{doctor_name} 의사 비대면 진료 ({'초진' if visit_type == 'first' else '재진'})",
                       amount=amount, status="paid", method="데모 결제", approved_at=a.completed_at))
        db.add(Review(appointment_id=a.id, patient_id=patient.id, doctor_id=doctor_id, wants_revisit=revisit,
                      tag_kind="kind" in tags, tag_detailed="detailed" in tags, tag_punctual="punctual" in tags, body=body,
                      created_at=a.completed_at + timedelta(hours=2)))
    return len(PAST_VISITS)


# 2차 질문·답변 (requirements 5). 일반적인 안내 수준으로, 진단처럼 읽히지 않게 쓴다
# (작성자, 진료과, 제목, 내용, 부위, 기간, 며칠 전, [(답변 의사, 답변, 대면 권유 진료과)])
DEMO_QUESTIONS = [
    ("jiwoo@demo.medion", "13", "아침마다 코가 막혀요", "일어나면 코가 막히고 재채기가 나요. 낮에는 좀 괜찮아요.", "코", "1m", 20, [
        ("seojin@demo.medion", "아침에 심해지는 코막힘은 실내 공기나 먼지, 온도 변화의 영향을 받는 경우가 많아요. 침구를 자주 세탁하고 실내 습도를 40~60%로 맞춰보세요. 증상이 계속되면 이비인후과 진료를 받아보시는 게 좋아요.", ["13"]),
    ]),
    ("minjae@demo.medion", "01", "부모님이 식후에 속이 더부룩하대요", "60대 어머니가 식사 후 더부룩하다고 하세요. 소화제를 드셔도 비슷하대요.", "배", "1-2w", 18, [
        ("doyoon@demo.medion", "식사를 천천히 하시고 기름진 음식은 잠시 줄여보세요. 연세가 있으시고 증상이 2주 넘게 이어지면 내과에서 한 번 확인받아 보시길 권해요.", ["01"]),
        ("chaewon@demo.medion", "식후 바로 눕지 않고 가볍게 걷는 것도 도움이 돼요. 체중이 줄거나 다른 증상이 생기면 꼭 병원에 가보세요.", []),
    ]),
    ("jiwoo@demo.medion", "14", "얼굴에 뾰루지가 자주 나요", "턱 쪽에 뾰루지가 반복해서 나요. 손으로 짜면 더 번지는 것 같아요.", "얼굴", "longer", 15, [
        ("jian@demo.medion", "손으로 짜면 흉이 남거나 번질 수 있어 피하시는 게 좋아요. 순한 세안제로 하루 두 번 세안하고 보습을 챙겨보세요. 오래 반복되면 피부과에서 상담받아 보세요.", []),
    ]),
    ("minjae@demo.medion", "05", "오래 앉아 있으면 허리가 뻐근해요", "사무직인데 오후만 되면 허리가 뻐근해요.", "허리", "1m", 12, [
        ("maru@demo.medion", "한 시간에 한 번은 일어나서 가볍게 스트레칭해 보세요. 의자 높이와 모니터 높이도 확인해보시고요. 다리가 저리거나 통증이 심해지면 대면 진료가 필요해요.", ["05"]),
        ("hajun@demo.medion", "허리와 엉덩이 근육 스트레칭을 꾸준히 하면 도움이 될 수 있어요. 무리한 운동보다는 걷기부터 시작해보세요.", []),
    ]),
    ("jiwoo@demo.medion", "12", "눈이 자주 건조하고 뻑뻑해요", "모니터를 오래 보면 눈이 뻑뻑하고 따가워요.", "눈", "1-2w", 9, [
        ("bom@demo.medion", "화면을 볼 때는 20분마다 20초 정도 먼 곳을 보면서 눈을 쉬게 해주세요. 실내가 건조하면 가습기도 도움이 돼요. 눈이 충혈되거나 시야가 흐려지면 안과 진료를 받아보세요.", []),
    ]),
    ("minjae@demo.medion", "11", "아이가 밤에 기침을 해요", "5살 아이가 낮에는 괜찮은데 밤에 기침을 해요. 열은 없어요.", "목", "today", 6, [
        ("serin@demo.medion", "열이 없고 잘 놀면 우선 따뜻한 물을 자주 먹이고 방을 촉촉하게 해주세요. 숨쉬기 힘들어하거나 열이 나면 바로 소아청소년과에 가보세요.", ["11"]),
    ]),
    ("jiwoo@demo.medion", "03", "요즘 잠들기가 어려워요", "누우면 생각이 많아져서 1시간 넘게 잠이 안 와요.", None, "1-2w", 4, [
        ("iden@demo.medion", "자기 전 1시간은 휴대폰을 멀리하고, 매일 같은 시간에 일어나는 것부터 시작해보세요. 낮잠과 늦은 카페인도 줄여보시고요. 2주 넘게 이어지면 상담을 받아보시는 걸 권해요.", []),
    ]),
    ("minjae@demo.medion", "23", "환절기마다 컨디션이 떨어져요", "날씨가 바뀔 때마다 피곤하고 목이 칼칼해요.", None, "1m", 2, [
        ("haram@demo.medion", "충분히 자고 물을 자주 드세요. 실내 환기와 손 씻기도 도움이 돼요. 열이 나거나 증상이 오래가면 진료를 받아보세요.", []),
    ]),
    # 답변 대기 (의사 질문함 시연용)
    ("jiwoo@demo.medion", "01", "속이 쓰리고 신물이 올라와요", "저녁을 늦게 먹으면 속이 쓰려요. 어떻게 하면 좋을까요?", "배", "1-2w", 1, []),
    ("minjae@demo.medion", "14", "손등이 건조해서 갈라져요", "손을 자주 씻어서 그런지 손등이 갈라지고 따가워요.", "손", "1-2w", 1, []),
    ("jiwoo@demo.medion", None, "어느 과로 가야 할지 모르겠어요", "가끔 어지럽고 머리가 무거워요. 어느 진료과에 가야 하나요?", "머리", "today", 0, []),
]


def seed_questions(db: Session) -> int:
    """질문·답변 시드. 질문이 하나도 없을 때만 넣는다."""
    if db.scalar(select(Question.id).limit(1)):
        return 0
    ids = dict(db.execute(select(User.email, User.id)).all())
    now = datetime.now(UTC)
    for author, dept, title, body, part, duration, days_ago, answers in DEMO_QUESTIONS:
        created = now - timedelta(days=days_ago, hours=3)
        q = Question(author_id=ids[author], department_code=dept, title=title, body=body, body_part=part,
                     duration=duration, visibility="public", status="answered" if answers else "waiting",
                     answer_count=len(answers), created_at=created, updated_at=created)
        db.add(q)
        db.flush()
        for n, (doctor, text, depts) in enumerate(answers):
            a = Answer(question_id=q.id, doctor_id=ids[doctor], body=text, recommends_visit=bool(depts),
                       helpful_count=0, created_at=created + timedelta(hours=2 + n))
            db.add(a)
            db.flush()
            db.add_all(AnswerRecommendedDepartment(answer_id=a.id, department_code=c) for c in depts)
    return len(DEMO_QUESTIONS)


# 복용 중인 약 (P-1 시연용): 한지우가 그제 진료받고 어제 약을 받은 처방. 후기는 비워둬서 후기 작성도 시연할 수 있다
ACTIVE_RX_CODE = "RX-DEMO-0001"


def seed_active_medication(db: Session) -> int:
    if db.scalar(select(Prescription.id).where(Prescription.code == ACTIVE_RX_CODE)):
        return 0
    ids = dict(db.execute(select(User.email, User.id)).all())
    patient = db.get(User, ids["jiwoo@demo.medion"])
    doctor_id = ids["seojin@demo.medion"]
    start = datetime.now(KST).replace(hour=19, minute=0, second=0, microsecond=0) - timedelta(days=2)
    start = start.astimezone(UTC)
    a = Appointment(
        patient_id=patient.id, doctor_id=doctor_id, subject_name=patient.nickname, subject_birth_year=patient.birth_year,
        subject_gender=patient.gender, start_at=start, end_at=start + timedelta(minutes=30), slot_key=start,
        status="completed", visit_type="return", symptom_note="콧물과 코막힘이 있어요",
        doctor_summary="코 점막이 부어 있는 상태로 보여요. 약을 드시고 실내 습도를 맞춰주세요. 일주일 넘게 이어지면 대면 진료를 받아보세요.",
        started_at=start, completed_at=start + timedelta(minutes=15),
    )
    db.add(a)
    db.flush()
    drugs = dict(db.execute(select(Drug.name, Drug.id)).all())
    db.add(Prescription(appointment_id=a.id, code=ACTIVE_RX_CODE, issued_at=a.completed_at, note="식후 30분에 드세요",
                        items=[PrescriptionItem(drug_id=drugs["데모코막힘정"], dose="1정", times_per_day=3, days=5, instruction="식후 30분"),
                               PrescriptionItem(drug_id=drugs["데모비염캡슐"], dose="1캡슐", times_per_day=1, days=5, instruction="아침 식후")]))
    _, amount = fee_for(start.astimezone(KST).year - patient.birth_year, "return")
    db.add(Payment(appointment_id=a.id, patient_id=patient.id, order_id=_new_order_id(a.id),
                   order_name="박서진 의사 비대면 진료 (재진)", amount=amount, status="paid", method="데모 결제",
                   approved_at=a.completed_at))
    db.add(PharmacyOrder(appointment_id=a.id, pharmacy_ext_id="SAMPLE1", pharmacy_name="봄빛약국",
                         pharmacy_address="광주광역시 서구 (데모 주소)", receive_method="pickup", status="received",
                         status_changed_at=a.completed_at + timedelta(hours=16)))
    return 1


def seed_drugs(db: Session) -> int:
    existing = set(db.scalars(select(Drug.name)))
    new = [Drug(name=name, maker=maker, form=form) for name, maker, form in DEMO_DRUGS if name not in existing]
    db.add_all(new)
    return len(new)


def seed_departments(db: Session) -> int:
    existing = set(db.scalars(select(Department.code)))
    added = 0
    for order, (code, name) in enumerate(DEPARTMENTS):
        if code not in existing:
            db.add(Department(code=code, name=name, sort_order=order))
            added += 1
    return added


def seed_demo_users(db: Session) -> int:
    existing = set(db.scalars(select(User.email)))
    password_hash = hash_password(DEMO_PASSWORD)
    added = 0

    for email, nickname, role, birth_year, gender in DEMO_USERS:
        if email in existing:
            continue
        db.add(User(email=email, password_hash=password_hash, nickname=nickname, role=role,
                    birth_year=birth_year, gender=gender, is_demo=True))
        added += 1

    now = datetime.now(UTC)
    for email, name, dept, hospital, status, bio, _ in DEMO_DOCTORS:
        if email in existing:
            continue
        doctor = User(email=email, password_hash=password_hash, nickname=name, role="doctor", is_demo=True)
        db.add(doctor)
        db.flush()  # doctor.id 를 받기 위해
        db.add(DoctorProfile(
            user_id=doctor.id, name=name, department_code=dept, hospital_name=hospital, bio=bio,
            license_number="00000",  # 가상 면허번호
            verification_status=status, submitted_at=now,
            reviewed_at=now if status == "approved" else None,
        ))
        added += 1
    return added


def seed_schedules(db: Session) -> int:
    """진료 시간표가 없는 시연용 의사에게 시간표를 넣는다."""
    with_schedule = set(db.scalars(select(DoctorSchedule.doctor_id)))
    added = 0
    for email, *_, plan in DEMO_DOCTORS:
        doctor_id = db.scalar(select(User.id).where(User.email == email))
        if plan is None or doctor_id is None or doctor_id in with_schedule:
            continue
        for weekday, start, end, lunch_start, lunch_end in SCHEDULES[plan]:
            db.add(DoctorSchedule(
                doctor_id=doctor_id, weekday=weekday,
                start_time=time.fromisoformat(start), end_time=time.fromisoformat(end),
                lunch_start=time.fromisoformat(lunch_start) if lunch_start else None,
                lunch_end=time.fromisoformat(lunch_end) if lunch_end else None,
            ))
        added += 1
    return added


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="시연용 데이터를 지우고 다시 입력")
    args = parser.parse_args()

    with SessionLocal() as db:
        if args.reset:
            # TODO(A-5): 시연용 계정이 만든 예약·결제·처방전·후기·알림 삭제 (5단계 이후)
            pass
        departments = seed_departments(db)
        db.flush()  # 의사 프로필이 진료과를 참조하므로 먼저 반영
        users = seed_demo_users(db)
        db.flush()
        schedules = seed_schedules(db)
        drugs = seed_drugs(db)
        documents = seed_doctor_documents(db)
        visits = seed_past_visits(db)
        db.flush()
        medication = seed_active_medication(db)
        questions = seed_questions(db)
        db.commit()
    print(f"진료과 {departments}개, 시연용 계정 {users}개, 진료 시간표 {schedules}명, 데모 약 {drugs}개, "
          f"심사 서류 {documents}개, 지난 진료·후기 {visits}건, 복용 중인 처방 {medication}건, 질문 {questions}개 추가 "
          f"(비밀번호: {DEMO_PASSWORD})")


if __name__ == "__main__":
    main()
