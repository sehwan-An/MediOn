# MediON — 기술 설계 (tech-spec.md)

> 기획은 [idea.md](./idea.md), 기능 목록과 ID(A-1, I-3 …)는 [requirements.md](./requirements.md) 참고
> 이 문서는 **어떻게 만드는가**를 다룹니다. 개발하면서 계속 업데이트합니다.
> 표시: **[1차]** 비대면진료 흐름 · **[2차]** 질문·답변 · **[보류]** 화상통화

---

## 1. 아키텍처

```
┌─────────────────────┐        HTTPS (JSON, JWT)        ┌───────────────────────┐
│  Frontend (Vercel)  │ ──────────────────────────────▶ │  Backend (Render)     │
│  React + Vite       │ ◀────────────────────────────── │  FastAPI              │
│  카카오맵 JS SDK     │                                 │  ┌─────────────────┐  │
│  토스 결제위젯 SDK   │                                 │  │ SQLAlchemy      │──┼──▶ MariaDB(개발) / MySQL 8(배포)
└─────────────────────┘                                 │  └─────────────────┘  │
     │          │                                       │  ┌─────────────────┐  │
     │          └──▶ 토스 결제창 (테스트)                 │  │ httpx           │──┼──▶ 토스페이먼츠 결제 승인 API
     ▼                                                  │  │ (외부 API)       │──┼──▶ 약국 정보 (공공데이터포털)
 카카오맵 서버                                            │  └─────────────────┘  │──▶ [2차] 심평원 병원정보
                                                        └───────────────────────┘
```

- 프론트는 **화면 표시**만 담당하고, 금액 계산·상태 변경·권한 판단은 모두 백엔드가 합니다.
- 비밀 키(토스 시크릿 키, 공공데이터 인증키, JWT 키)는 백엔드에만 있습니다.
- 브라우저에 노출되는 키는 카카오맵 JavaScript 키와 토스 **클라이언트** 키뿐입니다. 카카오 키는 콘솔에서 허용 도메인을 등록해 보호합니다.

## 2. 기술 스택

### 프론트엔드
| 항목 | 선택 | 이유 |
|---|---|---|
| 빌드 | Vite | 빠른 개발 서버 |
| 언어 | JavaScript | 익숙한 언어로 기능 완성에 집중 |
| 라우팅 | React Router | 역할별 라우트 보호 |
| 서버 데이터 | TanStack Query + axios | 캐싱, 로딩/에러 상태, 상태 polling(`refetchInterval`) |
| 로그인 상태 | React Context | 로그인 사용자와 역할 정도만 전역 관리 |
| 스타일 | Tailwind CSS v4 (`@tailwindcss/vite`) | 상태별 스타일이 많은 UI를 빠르게 구성, 토큰을 `@theme`으로 관리 |
| 지도 | 카카오맵 JS SDK | 국내 지도 |
| 결제 | 토스페이먼츠 결제위젯 SDK (테스트 키) | 실제 결제와 같은 흐름, 돈은 나가지 않음 |

### 백엔드
| 항목 | 선택 | 이유 |
|---|---|---|
| 프레임워크 | FastAPI | 자동 API 문서(`/docs`), Pydantic 검증 |
| DB | 개발 MariaDB 11.4 / 배포 MySQL 8 | PC에 설치된 MariaDB·HeidiSQL로 바로 개발. 두 DB 가 공통으로 지원하는 기능만 사용 |
| DB 드라이버 | PyMySQL (+ cryptography) | 순수 파이썬이라 Windows 설치가 쉬움, MySQL 8 기본 로그인 방식 지원 |
| ORM | SQLAlchemy 2.0 | 관계형 모델링, 트랜잭션 |
| 마이그레이션 | Alembic | 스키마 변경 이력 관리 |
| 검증 | Pydantic v2 | 요청/응답 스키마 |
| 인증 | PyJWT, bcrypt | 토큰 발급·검증, 비밀번호 해시 |
| 외부 API | httpx, xmltodict | 토스 승인, 공공데이터(XML) 호출 |
| 시간대 | `timezone(timedelta(hours=9))` | 진료 시간표는 한국 시간 기준. 한국은 서머타임이 없어 +09:00 고정으로 충분 (tzdata 불필요) |
| 테스트 | pytest, FastAPI TestClient | 권한·상태 변경·동시성 테스트 |

### 인프라 (데모)
| 항목 | 선택 | 메모 |
|---|---|---|
| 프론트 배포 | Vercel | |
| 백엔드 배포 | Render (무료) | 요청이 없으면 잠듦 → 11. 배포 참고 |
| DB | Aiven for MySQL (무료, 1GB) | 한동안 사용이 없으면 꺼질 수 있어 시연 전 확인 |
| 파일 저장 | 개발: 로컬 `uploads/` · 배포: Cloudinary (무료) | 의사 인증 서류, [2차] 질문 사진 |

## 3. 폴더 구조

```
MediOn/
├── README.md
├── CLAUDE.md
├── docs/                          # idea.md, requirements.md, tech-spec.md
├── frontend/
│   └── src/
│       ├── main.jsx, App.jsx       # App.jsx: 라우터 정의
│       ├── api/                   # 기능별 API 함수 (client.js: baseURL, JWT 헤더, 401 처리)
│       │   ├── auth.js  doctors.js  appointments.js  payments.js
│       │   ├── prescriptions.js  pharmacies.js  reviews.js  notifications.js
│       │   └── [2차] questions.js  answers.js  hospitals.js
│       ├── context/               # AuthProvider, useAuth
│       ├── routes/                # RoleRoute(역할 보호), StartGate(첫 방문 → 시작 화면), homePath
│       ├── components/
│       │   ├── layout/            # AppLayout(휴대폰 프레임), TabLayout, BottomNav, TopBar, DemoBanner
│       │   ├── ui/                # Button, Chip, StatusBadge, Icon, States(로딩·에러·빈 상태)
│       │   ├── doctor/            # DoctorCard, SlotPicker, FeeTable
│       │   ├── appointment/       # AppointmentCard, ProgressSteps
│       │   └── map/               # KakaoMap (약국·[2차] 병원 공용)
│       ├── pages/
│       │   ├── welcome/  login/  signup/  admin/  notifications/
│       │   ├── home/              # 증상 카테고리
│       │   ├── doctors/           # 의사 목록, 의사 상세, 예약하기
│       │   ├── appointments/      # 진료 내역, 예약 상세, 예약 완료, 후기 작성
│       │   ├── payments/          # 결제, 성공, 실패
│       │   ├── prescriptions/     # 처방전, 약국 선택
│       │   ├── my/                # 마이, 가족 관리, 결제 내역
│       │   ├── doctor/            # 의사: 진료 일정, 예약 상세, 진료 완료·처방, 시간표, 마이, 심사 중
│       │   └── [2차] qna/  question/  hospitals/
│       ├── constants/             # departments.js (백엔드와 코드 일치)
│       ├── utils/                 # storage.js(localStorage try/catch), datetime.js(한국 시간 표시)
│       └── index.css              # Tailwind + @theme 디자인 토큰
└── backend/
    ├── requirements.txt, .env.example, alembic.ini, alembic/versions/
    ├── scripts/seed.py            # 시드 데이터 입력·초기화
    ├── tests/
    └── app/
        ├── main.py                # 앱 생성, CORS, 공통 에러, 라우터 등록
        ├── core/                  # config, security(JWT·비밀번호), deps(get_db·권한), errors
        ├── db/                    # base, session(UTC 고정), types(UTCDateTime)
        ├── constants/             # categories.py(증상 카테고리), fees.py(진료비 표)
        ├── models/                # SQLAlchemy 모델
        ├── schemas/               # Pydantic 요청/응답
        ├── routers/
        │   ├── auth.py  doctors.py  appointments.py  doctor_console.py
        │   ├── payments.py  prescriptions.py  pharmacies.py  reviews.py
        │   ├── family.py  notifications.py  admin.py
        │   └── [2차] questions.py  answers.py  hospitals.py
        └── services/              # 비즈니스 로직
            ├── slot_service.py          # 예약 가능 시간 계산
            ├── appointment_service.py   # 예약·취소·진료 시작/완료 (트랜잭션)
            ├── fee_service.py           # 진료비 계산
            ├── payment_service.py       # 토스 승인 (서버 금액 검증)
            ├── pharmacy_service.py      # 약국 조회·전송·상태
            ├── toss_client.py           # 토스 API 호출
            ├── pharmacy_client.py       # 약국 공공데이터 API 호출·캐시
            └── [2차] question_service.py  answer_service.py  hira_client.py
```

**규칙**: router 는 요청을 받고 응답만 돌려줍니다. 권한 확인 외의 판단(금액 계산, 상태 변경, 알림 생성)은 `services/` 에 둡니다.

### 디자인 토큰 (Tailwind `@theme`)

컴포넌트에서는 `bg-primary`, `text-ink-muted`처럼 토큰 이름으로만 씁니다. 피그마 변수(MediON 컬렉션)와 같은 이름입니다.

```css
@theme {
  --font-sans: "Noto Sans KR", sans-serif;
  --color-primary: #0A62E0;        /* 환자 화면 주요 버튼 */
  --color-primary-soft: #E7F0FF;
  --color-doctor: #1B3A73;         /* 의사 화면 주요 버튼·헤더 */
  --color-doctor-soft: #EAF0FA;
  --color-ink: #0F1B2D;            /* 본문 */
  --color-ink-muted: #5B6675;      /* 보조 텍스트 */
  --color-line: #E3E8EF;           /* 구분선·테두리 */
  --color-surface: #F4F6F9;        /* 페이지 배경 */
  --color-wait: #6B3A00;           /* 대기·주의 상태 */
  --color-wait-soft: #FFF1E0;
  --color-done: #0A4BAA;           /* 완료 상태 */
  --color-done-soft: #E7F0FF;
}
```

- 상태 색은 빨강/초록 대신 **주황(대기)/파랑(완료)**으로 구분합니다 (색약 고려).
- 터치 영역은 최소 44px (`min-h-11`). 넓은 화면에서는 390×844 휴대폰 프레임 안에 표시합니다.

## 4. DB 설계

### MySQL · MariaDB 공통 규칙

- 개발은 MariaDB 11.4(PC), 배포는 MySQL 8(Aiven). **두 DB 가 모두 지원하는 기능만 씁니다.** `tests/test_mysql.py` 는 두 DB 에서 모두 통과해야 합니다.
- DB 와 모든 테이블은 `utf8mb4` / `utf8mb4_unicode_ci`
- 시간은 모두 **UTC** 로 저장합니다. 접속 시 세션 시간대를 `+00:00` 으로 고정하고(`db/session.py`), 컬럼 타입 `UTCDateTime` 이 UTC 로 저장·UTC 시간대를 붙여 반환합니다(`db/types.py`).
- **한국 시간이 필요한 계산**(진료 시간표, "오늘", 나이)은 서버에서 `Asia/Seoul` 로 바꿔 계산한 뒤 UTC 로 저장합니다. 화면 표시는 프론트가 브라우저 시간대로 바꿉니다.
- MySQL 은 오래 쉰 연결을 끊으므로 `pool_recycle=3600`. downgrade 에서 외래 키가 쓰는 인덱스를 따로 지우지 않습니다 (error 1553).
- 부분 유니크 인덱스(`WHERE` 조건)는 MySQL·MariaDB 모두 지원하지 않습니다. 필요한 곳은 **NULL 을 이용한 유니크**로 대신합니다 (아래 `appointments.slot_key`).

### ERD

```
users 1──0..1 doctor_profiles ──N:1── departments
  │                │ 1
  │                ├──N doctor_schedules        (요일별 진료 시간)
  │                └──N doctor_documents        (인증 서류)
  │ 1
  ├──N family_members
  │ 1                     N
  ├──N appointments ──────── 1 doctor(users)
  │        │ 1
  │        ├──0..1 payments
  │        ├──0..1 prescriptions ──1──N prescription_items ──N:1── drugs
  │        │             └──0..1 pharmacy_orders
  │        └──0..1 reviews
  └──N notifications

pharmacies_cache (외부 API 응답 캐시, 독립)
[2차] questions ─ question_images, answers ─ answer_recommended_departments, helpful_votes, hospitals_cache
```

### 테이블 — 이미 만든 것

**users** · **doctor_profiles** · **doctor_documents** · **departments**: 1단계에서 만든 그대로입니다. (첫 마이그레이션 `8d3091b2b274`)

| 테이블 | 주요 컬럼 |
|---|---|
| users | id, email(unique), password_hash, nickname, role(`patient`/`doctor`/`admin`), birth_year, gender, is_demo, created_at |
| doctor_profiles | user_id(PK), name, department_code, hospital_name, bio, license_number, verification_status(`pending`/`approved`/`rejected`), rejected_reason, submitted_at, reviewed_at |
| doctor_documents | id, doctor_id, type(`license`/`specialist`/`employment`), file_key(비공개 경로), created_at |
| departments | code(심평원 진료과목 코드), name, sort_order |

> 인증 서류는 공개 URL로 저장하지 않고, 관리자 API(`GET /admin/doctors/{id}/documents/{doc_id}`, 관리자 토큰 필요·캐시 금지)로만 내려줍니다. 파일 이름은 추측할 수 없는 임의 값이고, 형식은 확장자가 아니라 파일 앞부분(매직 넘버)으로 검사합니다(JPG·PNG·WEBP·PDF, 5MB). 면허 진위를 확인할 공개 API가 없어 서류 제출 + 관리자 수동 승인으로 처리합니다.

### 테이블 — [1차] 새로 만들 것

**doctor_schedules** (I-1)
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | int PK | |
| doctor_id | int FK → users | |
| weekday | smallint | 0=월 … 6=일 |
| start_time, end_time | time | 한국 시간 기준 (예: 09:00, 18:00) |
| lunch_start, lunch_end | time null | 점심시간 |

유니크: `(doctor_id, weekday)` · 예약 단위는 30분 (`SLOT_MINUTES = 30` 상수)

**family_members** (I-5, I-6)
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | int PK | |
| owner_id | int FK → users | 등록한 환자 |
| name | varchar(30) | |
| relation | varchar(10) | `parent` / `child` / `spouse` / `other` |
| birth_date | date | 진료비 계산용 |
| gender | varchar(1) null | |
| created_at | datetime (UTC) | |

**appointments** (I, J)
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | int PK | |
| patient_id | int FK → users | 예약한 계정 |
| family_member_id | int FK null | null 이면 본인 진료 · **가족 예약(I-5) 때 추가** |
| subject_name | varchar(30) | 진료받는 사람 이름 (예약 시점 값 복사) |
| subject_birth_year | smallint | 진료비 계산용 (예약 시점 값 복사). 가입 정보가 출생연도라서 연도만 저장 |
| subject_gender | varchar(1) null | |
| doctor_id | int FK → users | |
| start_at, end_at | datetime (UTC) | 30분 단위 |
| **slot_key** | datetime (UTC) null | 활성 예약이면 `start_at` 과 같은 값, 취소되면 **NULL** |
| status | varchar(12) | `booked` / `in_progress` / `completed` / `cancelled` |
| visit_type | varchar(6) | `first`(초진) / `return`(재진), 예약 시 판정 |
| symptom_note | varchar(500) null | 증상 메모 |
| doctor_summary | text null | 진료 요약 (환자에게 보이는 안내) |
| cancelled_by | varchar(8) null | `patient` / `doctor` |
| cancel_reason | varchar(200) null | |
| started_at, completed_at, cancelled_at | datetime (UTC) null | cancelled_at 만 5단계, 나머지는 6단계에서 추가 |
| question_id | int FK null | [2차] 질문에서 온 예약 (C-7) |
| created_at | datetime (UTC) | |

- **유니크 `(doctor_id, slot_key)`** → 같은 의사·같은 시간에 활성 예약은 하나만 존재 (I-3). 유니크 인덱스는 NULL 을 여러 개 허용하므로 취소된 예약끼리는 겹쳐도 됩니다.
- 인덱스: `(patient_id, start_at)` 진료 내역, `(doctor_id, start_at)` 진료 일정
- 진료받는 사람 정보를 복사해 두는 이유: 나중에 가족 정보를 고쳐도 과거 진료 기록·진료비가 바뀌지 않게

**payments** (K)
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | int PK | |
| appointment_id | int FK unique | 진료 1건에 결제 1건 |
| patient_id | int FK → users | |
| order_id | varchar(64) unique | 서버가 만드는 주문번호 (예: `medion-apt-42-a1b2c3`) |
| order_name | varchar(100) | "김도윤 의사 비대면 진료 (초진)" |
| amount | int | **서버가 계산한 금액** (원) |
| status | varchar(10) | `ready` / `paid` / `failed` |
| payment_key | varchar(200) null unique | 토스가 준 결제 키 |
| method | varchar(30) null | 카드, 간편결제 등 |
| receipt_url | varchar(500) null | |
| fail_code, fail_message | varchar null | |
| approved_at | datetime (UTC) null | |
| created_at | datetime (UTC) | |

**drugs** (L-1, 시드 데이터)
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | int PK | |
| item_code | varchar(20) null | 식약처 품목기준코드 (있으면) |
| name | varchar(100) | 제품명 |
| maker | varchar(60) | 제조사 |
| form | varchar(20) | 정, 캡슐, 시럽, 연고 등 |

인덱스: `(name)` — 처방전 작성 시 이름 검색 (`LIKE '감기%'`)

**prescriptions** (L)
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | int PK | |
| appointment_id | int FK unique | |
| code | varchar(20) unique | 처방전 번호 (예: `RX-20261030-0042`) |
| issued_at | datetime (UTC) | |
| note | varchar(300) null | 전체 복용 안내 |

**prescription_items**
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | int PK | |
| prescription_id | int FK | |
| drug_id | int FK → drugs | |
| dose | varchar(20) | 1회 투약량 (예: "1정") |
| times_per_day | smallint | 1일 투여 횟수 |
| days | smallint | 투약 일수 (초진 최대 7, L-2) |
| instruction | varchar(100) null | "식후 30분" 등 |

**pharmacy_orders** (M)
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | int PK | |
| appointment_id | int FK unique | 진료(처방전) 1건은 약국 1곳에만 전송. 구현에서는 예약 id 로 묶었다 |
| pharmacy_ext_id | varchar(20) | 공공데이터 약국 ID |
| pharmacy_name, pharmacy_address, pharmacy_tel | varchar | 전송 시점 값 복사 |
| pharmacy_lat, pharmacy_lng | decimal(9,6) | |
| receive_method | varchar(10) | `pickup` / `delivery` |
| delivery_reason | varchar(20) null | `remote_area` / `long_term_care` / `disability` / `rare_disease` |
| delivery_address | varchar(200) null | |
| status | varchar(10) | `sent` / `preparing` / `ready` / `shipping` / `received` |
| status_changed_at | datetime (UTC) | |
| created_at | datetime (UTC) | |

**reviews** (N)
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | int PK | |
| appointment_id | int FK unique | 진료 1건에 후기 1개 |
| patient_id, doctor_id | int FK | |
| wants_revisit | boolean | 재진 희망 |
| tag_kind, tag_detailed, tag_punctual | boolean | 친절한 진료 / 자세한 설명 / 예약 시간 준수 |
| body | varchar(500) null | |
| created_at | datetime (UTC) | |

**notifications** (F) — 1단계에서 만든 테이블에 컬럼 추가
| 컬럼 | 변경 | 설명 |
|---|---|---|
| type | 값 추가, varchar(20)→(30) | `appointment_booked` / `appointment_cancelled` / `consultation_started` / `payment_requested` / `pharmacy_status` / `doctor_approved` / `doctor_rejected` / [2차] `answer_arrived` |
| appointment_id | **새 컬럼** int FK null | 이동할 예약 |
| question_id | 그대로 | [2차] |

**pharmacies_cache** (M-1) — 1차 구현은 서버 메모리 캐시(`pharmacy_client._cache`)로 대신했다. 서버를 여러 대 띄울 때 이 테이블로 옮긴다
| 컬럼 | 타입 | 설명 |
|---|---|---|
| cache_key | varchar(100) PK | `lat:35.16:lng:126.85` (소수 2자리) |
| payload | json | 가공된 약국 목록 |
| fetched_at | datetime (UTC) | 24시간 뒤 다시 조회 |

**medication_checks** (P-2)
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | int PK | |
| patient_id | int FK | |
| prescription_id | int FK | |
| taken_on | date | 한국 날짜 |
| slot | varchar(10) | `morning` / `lunch` / `evening` / `bedtime` |
| created_at | datetime (UTC) | |
| | unique (prescription_id, taken_on, slot) | 같은 시간대 두 번 체크 방지 |

> 복용표 자체는 저장하지 않고 처방(1일 횟수·일수)과 약 수령 날짜(`pharmacy_orders.status_changed_at`, status=received)로 그때그때 계산합니다.

### 테이블 — [2차] 이미 만든 것

`questions`, `question_images`, `answers`, `answer_recommended_departments`, `helpful_votes`, `hospitals_cache` 는 1단계 마이그레이션에 이미 들어 있습니다. 2차 구현 전까지 사용하지 않습니다. 컬럼 설계는 git 기록의 이전 tech-spec 과 모델 코드(`app/models/`) 참고.

### 상수 (DB 대신 코드에 두는 것)

**진료비 표** `app/constants/fees.py` (K-1, 목업 기준 데모 금액)
| 나이 (진료일 기준 만 나이) | 초진 | 재진 |
|---|---|---|
| 1세 미만 | 1,200원 | 800원 |
| 1~64세 | 6,800원 | 5,100원 |
| 65세 이상 | 4,500원 | 1,700원 |

**증상 카테고리** `app/constants/categories.py` (H-1): 코드, 이름, 연결 진료과 목록. `GET /api/categories` 로 프론트에 제공. 목록은 requirements.md 4. 증상 카테고리 참고.

## 5. 인증과 권한

### 토큰
- 로그인 성공 시 **access token(JWT) 1개**, 유효기간 12시간. 데모라 refresh token 은 생략합니다.
- payload: `{ "sub": user_id, "role": "patient", "exp": ... }`
- 프론트는 `localStorage` 에 저장하고 `Authorization: Bearer` 로 보냅니다. 401 이면 로그아웃합니다. 실서비스라면 httpOnly 쿠키가 더 안전하다는 점을 README에 적어둡니다.

### 백엔드 권한 처리 (`core/deps.py`, 구현 완료)
- `get_optional_user`: 게스트도 되는 API
- `get_current_user`: 로그인 필수 (401)
- `require_role("patient")`: 역할 확인 (403)
- `require_verified_doctor`: 인증 승인된 의사만 (403 `DOCTOR_NOT_VERIFIED`)
- **소유권 확인**(내 예약인지, 내 환자의 예약인지)은 service 에서 하고, 남의 데이터는 **404** 로 숨깁니다.

### 권한 표 [1차]

| 동작 | 게스트 | 환자 | 인증 의사 | 심사 중 의사 |
|---|---|---|---|---|
| 의사 목록·상세·예약 가능 시간 보기 | O | O | O | O |
| 예약하기 | X | O | X | X |
| 내 예약 보기·취소 | X | 본인 것만 | X | X |
| 진료 일정 보기 | X | X | 자기 예약만 | X |
| 진료 시작·완료·처방전 작성 | X | X | 자기 예약만 | X |
| 의사 쪽 예약 취소 | X | X | 자기 예약, 진료 시작 전 | X |
| 결제·처방전 열람·약국 전송 | X | 본인 예약만 | X | X |
| 후기 작성 | X | 본인 완료 진료, 1회 | X | X |
| 의사 인증 심사 | X | X | X | X (관리자만) |

## 6. API 명세

공통: 접두사 `/api`, JSON, 날짜는 ISO 8601(UTC, `+00:00`). 목록은 `?page=1&size=20`.

### 인증 · 마이
| 메서드 | 경로 | 권한 | 설명 |
|---|---|---|---|
| POST | `/auth/signup` | 모두 | 일반 회원가입 (role=patient) |
| POST | `/auth/login` | 모두 | 로그인 → `{ access_token, user }` |
| POST | `/auth/signup/doctor` | 모두 | 의사 회원가입 신청 (multipart, 인증 서류). `pending` 으로 생성 |
| GET | `/auth/me` | 로그인 | 내 정보 (의사면 프로필·인증 상태) |
| PATCH | `/auth/me` | 로그인 | 프로필 수정 |
| GET | `/me/summary` | 로그인 | 마이 요약 (환자: 진료 횟수·결제 대기 / 의사: 이번 달 진료 수·재진 희망률) |
| GET·POST·DELETE | `/me/family`, `/me/family/{id}` | 환자 | 가족 관리 |

### 의사 찾기 (공개)
| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/categories` | 증상 카테고리와 연결 진료과 |
| GET | `/departments` | 진료과 목록 |
| GET | `/doctors` | `?category=cold` 또는 `?department=05`, `&available_today=true`, `&sort=revisit`. 인증 의사만. 각 의사에 `next_available_at`, `revisit_rate`, `review_count` 포함 |
| GET | `/doctors/{id}` | 의사 상세 + 진료 시간표 + 진료비 표 |
| GET | `/doctors/{id}/slots` | `?date=2026-10-30` (한국 날짜). 30분 단위 슬롯과 `available` 여부 |
| GET | `/doctors/{id}/reviews` | 후기 목록 + 재진 희망률·태그 통계 |

### 예약 (환자)
| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/appointments` | 예약하기 (7. 참고). 같은 시간 선점 시 409 `SLOT_TAKEN` |
| GET | `/appointments` | 내 진료 내역 `?tab=upcoming\|past\|cancelled` |
| GET | `/appointments/{id}` | 예약 상세 + 진행 단계 + 결제·처방전·약 수령 상태 요약 |
| POST | `/appointments/{id}/cancel` | `{ reason }`. `booked` 일 때만 |
| POST | `/appointments/{id}/review` | 후기 작성 (완료·결제된 진료, 1회) |

### 진료 (의사 콘솔)
| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/doctor/appointments` | `?date=2026-10-30` 진료 일정 |
| GET | `/doctor/appointments/{id}` | 예약 상세 + 이 환자의 이전 진료 |
| POST | `/doctor/appointments/{id}/start` | `booked` → `in_progress` |
| POST | `/doctor/appointments/{id}/complete` | 진료 완료 + 처방전 (7. 참고) |
| POST | `/doctor/appointments/{id}/cancel` | `{ reason }` 진료 시작 전만 |
| GET | `/doctor/schedule` | 내 진료 시간표 |
| GET | `/drugs` | `?q=타이레놀` 약 검색 (의사) |

### 결제 (환자)
| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/appointments/{id}/payment` | 결제 정보 `{ order_id, order_name, amount, status }`. 프론트는 이 값으로 토스 결제창을 엶 |
| POST | `/appointments/{id}/payment/demo` | 데모 결제: 토스 없이 서버 저장 금액으로 바로 paid (기본 모드, 두 번 눌러도 한 번만) |
| POST | `/payments/confirm` | `{ payment_key, order_id, amount }` → 서버 검증 후 토스 승인 (7. 참고) |
| POST | `/payments/fail` | `{ order_id, code, message }` 실패 기록 |
| GET | `/me/payments` | 결제 내역 |

### 처방전 · 약국 (환자)
| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/appointments/{id}/prescription` | 처방전. **결제 완료 전이면 403** `PAYMENT_REQUIRED` |
| GET | `/pharmacies` | `?lat=35.16&lng=126.85` 근처 약국 (캐시) |
| POST | `/appointments/{id}/pharmacy-order` | 약국 전송 `{ pharmacy: {ext_id, name, address, tel, lat, lng}, receive_method, delivery_reason?, delivery_address? }`. 이미 전송했으면 409 |
| POST | `/appointments/{id}/pharmacy-order/advance` | **데모 전용**: 다음 상태로 넘김 (M-5) |

### 알림 · 관리자 · 기타
| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/notifications` | `?unread=true` |
| GET | `/notifications/unread-count` | 30초마다 polling |
| PATCH | `/notifications/{id}/read` / POST `/notifications/read-all` | 읽음 처리 (남의 알림은 404) |
| GET | `/admin/doctors?status=pending` | 인증 신청 목록 (pending / approved / rejected) |
| GET | `/admin/doctors/{id}/documents/{doc_id}` | 서류 파일 (관리자만, `Cache-Control: no-store`) |
| PATCH | `/admin/doctors/{id}` | `{ action: approve \| reject, reason }`. 심사 중일 때만(아니면 409), 반려는 사유 필수. 같은 트랜잭션에서 의사에게 알림 |
| GET | `/health` | 서버 깨우기 (구현 완료) |

### [2차] 질문·답변 · 병원
공개 질문은 누구나, 비공개 질문은 작성자와 인증된 의사만 봅니다(아니면 404).

| 메서드 | 경로 | 권한 | 설명 |
|---|---|---|---|
| GET | `/questions?department=&q=` | 모두 | 상담 피드: 답변 달린 공개 질문, 최신순 (C-1~C-3) |
| GET | `/questions/{id}` | 모두 | 상세 + 답변(추천 진료과, 도움돼요 수, 내가 눌렀는지) |
| POST | `/questions` | 환자 | 질문 작성 `{ department_code?, title, body, body_part?, duration, visibility }` |
| DELETE | `/questions/{id}` | 작성자 | 삭제 (답변도 함께) |
| GET | `/me/questions?status=` | 환자 | 내 질문 + 상태별 개수 |
| GET | `/doctor/qna?mine_only=` | 인증 의사 | 답변 대기 질문, 오래 기다린 순 (D-1, D-2) |
| POST | `/questions/{id}/answers` | 인증 의사 | 답변 + 추천 진료과 + 질문 상태·답변 수 + 환자 알림을 한 트랜잭션. 의사당 1번(409) |
| GET | `/doctor/answers` | 인증 의사 | 내 답변 목록 (D-6) |
| POST | `/answers/{id}/helpful` | 환자 | 도움돼요 토글 → `{ helpful_count, helped }` |
| GET | `/hospitals` | 모두 | (아직 없음) 근처 병원 |

### 오늘 약 복용 (P)
| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/me/medications/today` | 오늘 복용표: 처방별 `{ day, total_days, slots: [{ slot, label, time, taken, drugs }] }` |
| POST | `/me/medications/check` | `{ prescription_id, slot, taken }` 오늘 시간대 체크/해제 → 오늘 복용표 |

### 예시

`GET /api/doctors/3/slots?date=2026-10-30`
```json
{
  "date": "2026-10-30",
  "slots": [
    { "start_at": "2026-10-30T00:00:00+00:00", "label": "09:00", "available": false },
    { "start_at": "2026-10-30T00:30:00+00:00", "label": "09:30", "available": true }
  ]
}
```

`POST /api/appointments`
```json
{
  "doctor_id": 3,
  "start_at": "2026-10-30T00:30:00+00:00",
  "family_member_id": null,
  "symptom_note": "계단을 내려갈 때 무릎이 시큰해요"
}
```
→ `201` `{ "id": 42, "status": "booked", "visit_type": "first", "start_at": "…" }`
→ `409` `{ "error": { "code": "SLOT_TAKEN", "message": "이미 예약된 시간이에요. 다른 시간을 선택해주세요" } }`

`POST /api/doctor/appointments/42/complete`
```json
{
  "summary": "무릎 앞쪽 통증은 … 무리한 계단 이용을 줄이고 …",
  "prescription": {
    "note": "식후 30분에 복용하세요",
    "items": [ { "drug_id": 12, "dose": "1정", "times_per_day": 3, "days": 5, "instruction": "식후" } ]
  }
}
```
처방이 없으면 `"prescription": null`

## 7. 핵심 로직

### 예약 가능 시간 계산 (`slot_service`)
1. 날짜(한국)의 요일로 `doctor_schedules` 조회 → 없으면 휴진
2. 시작~끝을 30분씩 나누고 점심시간 제외
3. 지금(한국 시간)보다 이른 슬롯 제외
4. 그날 `slot_key IS NOT NULL` 인 예약 시간 제외
5. 한국 시간 → UTC 로 바꿔 응답 (`label` 은 한국 시간 "09:30")

> 의사 목록의 `next_available_at` 은 오늘부터 7일 안에서 첫 번째 가능한 슬롯입니다.

### 예약하기 — 중복 예약 방지 (I-3)
`appointment_service.book()`

1. 요청한 `start_at` 이 실제 슬롯인지 검증 (시간표 안, 30분 단위, 미래) → 아니면 400 `INVALID_SLOT`
2. 진료받는 사람 결정: 본인이면 `users.birth_year` 필요(없으면 400 `BIRTH_YEAR_REQUIRED`, 예약 화면에서 출생연도를 받아 함께 저장), 가족이면 `family_members` (본인 소유가 아니면 404)
3. 초진·재진 판정: 같은 의사·같은 진료받는 사람의 `completed` 예약이 있으면 `return`
4. `slot_key = start_at` 으로 INSERT
5. **유니크 위반(IntegrityError) → 롤백 후 409 `SLOT_TAKEN`**
6. 같은 트랜잭션에서 의사에게 `appointment_booked` 알림

> 먼저 "비어 있는지 조회 → INSERT" 만 하면 두 요청이 동시에 조회를 통과해 둘 다 저장될 수 있습니다. 그래서 **최종 판정은 DB 유니크 제약**에 맡깁니다. 테스트에서 두 요청을 동시에 보내 하나만 성공하는지 확인합니다. 면접에서 설명하기 좋은 지점입니다.

### 예약 취소
- 환자: `booked` 이고 `start_at` 이전 → `status=cancelled`, **`slot_key=NULL`**(그 시간 다시 열림), 의사에게 알림
- 의사: `booked` 일 때 사유 필수, 환자에게 알림

### 진료 완료 — 하나의 트랜잭션 (J-4)
`appointment_service.complete()`

1. 내 예약이고 `in_progress` 인지 확인 → 아니면 404 / 409
2. 처방이 있으면: 초진이면 모든 항목 `days ≤ 7` 확인(L-2) → `prescriptions`, `prescription_items` 저장, 처방전 번호 생성
3. `status=completed`, `doctor_summary`, `completed_at`
4. 진료비 계산 → `payments` (`status=ready`, `order_id` 생성) 저장
5. 환자에게 `payment_requested` 알림
6. 커밋. 중간에 하나라도 실패하면 전부 취소

> "진료는 끝났는데 결제 요청이 안 생기는" 상황을 막습니다.

### 결제 승인 (K-3)
기본 모드는 데모 결제(`payment_service.demo_pay()`)라 아래 토스 흐름은 `VITE_PAYMENT_MODE=toss` 일 때만 씁니다.

`payment_service.confirm()`

```
프론트: GET /appointments/42/payment → { order_id, amount }
     → 토스 결제위젯 requestPayment({ orderId, orderName, successUrl, failUrl })
     → successUrl 로 돌아옴 (?paymentKey&orderId&amount)
     → POST /api/payments/confirm
서버:
  1. order_id 로 payments 조회, 내 결제인지 확인 (아니면 404)
  2. 이미 paid 이고 같은 payment_key → 그대로 성공 응답 (새로고침·중복 요청 대비)
  3. 요청 amount ≠ 저장된 amount → 400 AMOUNT_MISMATCH (토스 승인 호출 안 함)
  4. 토스 승인 API 호출: POST https://api.tosspayments.com/v1/payments/confirm
     Authorization: Basic base64("{TOSS_SECRET_KEY}:"), body { paymentKey, orderId, amount }
  5. 성공 → status=paid, payment_key, method, approved_at, receipt_url 저장
     실패 → status=failed, fail_code/message 저장, 400 으로 사유 전달
```

> 브라우저에서 넘어온 금액은 조작될 수 있으므로 **서버에 저장한 금액만 믿습니다.** 토스 테스트 키는 실제로 결제되지 않습니다. 정확한 요청·응답 필드는 토스페이먼츠 개발자센터 문서로 최종 확인합니다.

### 처방전 열람 조건
- `payments.status == paid` 일 때만 처방전 API 응답 (아니면 403 `PAYMENT_REQUIRED`)
- 응답에 `"is_demo": true` → 화면에 "데모 처방전" 워터마크

### 약국 전송과 상태 (M)
- 전송: 처방전 1장당 1건 (`prescription_id` 유니크, 두 번째는 409)
- 배송 선택 시 `delivery_reason` 필수 (대상자만)
- 상태 순서: 방문 `sent → preparing → ready → received`, 배송 `sent → preparing → shipping → received`
- `demo-advance` 는 다음 상태로 한 칸만 넘기고 환자에게 `pharmacy_status` 알림

### 진행 단계 계산 (예약 상세 I-8)
서버가 `steps` 배열로 내려주고 프론트는 그리기만 합니다.
```json
"steps": [
  { "key": "booked", "label": "예약", "state": "done" },
  { "key": "consultation", "label": "진료", "state": "done" },
  { "key": "payment", "label": "결제", "state": "current" },
  { "key": "prescription", "label": "처방전", "state": "todo" },
  { "key": "pharmacy", "label": "약 수령", "state": "todo" }
]
```
처방이 없으면 처방전·약 수령 단계는 `skipped`.

## 8. 외부 API 연동

| 대상 | 용도 | 호출 위치 | 메모 |
|---|---|---|---|
| 토스페이먼츠 | 결제 승인 | `services/toss_client.py` | 테스트 시크릿 키. 타임아웃 10초 |
| 약국 정보 (공공데이터포털, 국립중앙의료원 전국 약국 정보 조회 서비스) | 위치 기반 약국 목록 | `services/pharmacy_client.py` | XML → dict. 요청 파라미터는 공공데이터포털 문서로 확인 |
| 카카오맵 | 지도·마커 | 프론트 | 위치 거부 시 광주광역시청 좌표 |
| [2차] 심평원 병원정보서비스 | 진료과별 병원 | `services/hira_client.py` | |
| (Could) 식약처 의약품 API | 약 정보 (L-4) | | 1차 처방전 작성은 시드 `drugs` 테이블로 검색 |

공통 규칙
- 외부 API 는 `services/*_client.py` 에서만 호출합니다.
- 공공데이터는 **24시간 캐시**(`pharmacies_cache` 등), 실패·타임아웃(5초) 시 오래된 캐시라도 반환하고 없으면 503 "약국 정보를 잠시 불러올 수 없어요".
- 키가 비어 있으면(개발 초기) **시드에 넣은 샘플 약국 목록**을 돌려줘서 화면 개발을 막지 않습니다.

## 9. 에러 응답

```json
{ "error": { "code": "SLOT_TAKEN", "message": "이미 예약된 시간이에요. 다른 시간을 선택해주세요" } }
```

| HTTP | 언제 | 대표 코드 |
|---|---|---|
| 400 | 입력값 오류, 규칙 위반 | `VALIDATION_ERROR`, `AGREEMENT_REQUIRED`, `INVALID_SLOT`, `INVALID_DATE`, `BIRTH_YEAR_REQUIRED`, `AMOUNT_MISMATCH`, `DAYS_LIMIT` |
| 401 | 토큰 없음·만료, 로그인 실패 | `UNAUTHORIZED`, `TOKEN_EXPIRED`, `INVALID_TOKEN`, `INVALID_CREDENTIALS` |
| 403 | 역할 불일치, 결제 전 처방전 | `FORBIDDEN`, `DOCTOR_NOT_VERIFIED`, `PAYMENT_REQUIRED` |
| 404 | 대상 없음 (남의 예약도 404 로 숨김) | `NOT_FOUND` |
| 409 | 중복·상태 충돌 | `EMAIL_TAKEN`, `SLOT_TAKEN`, `INVALID_STATUS`, `ALREADY_SENT`, `ALREADY_REVIEWED` |
| 502 | 토스 승인 실패 | `PAYMENT_FAILED` |
| 503 | 외부 API 장애 | `SERVICE_UNAVAILABLE` |

프론트는 `message` 를 그대로 보여주고, 401 은 로그인 화면으로 보냅니다.

- 스키마에서 `ValueError("한국어 문장")` 으로 막은 입력 오류는 그 문장이 `message` 로 나갑니다 (예: "비밀번호는 8자 이상, 영문과 숫자를 섞어주세요"). 그 외 형식 오류는 "입력값을 확인해주세요".
- 로그인 실패는 이메일이 없는지, 비밀번호가 틀렸는지 구분하지 않고 같은 메시지를 줍니다.

## 10. 환경 변수

**backend/.env** (자세한 설명은 `backend/.env.example`)
```
DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME   # 개발 DB
DATABASE_URL=                                      # 배포: 있으면 DB_* 대신 사용
JWT_SECRET=, JWT_EXPIRE_HOURS=12
CORS_ORIGINS=http://localhost:5173
TOSS_SECRET_KEY=                                   # [1차 7단계] 토스 테스트 시크릿 키 (test_sk_…)
DATA_GO_KR_SERVICE_KEY=                            # [1차 8단계] 공공데이터포털 인증키 (약국·병원 공용)
UPLOAD_BACKEND=local, CLOUDINARY_URL=
```

**frontend/.env**
```
VITE_API_BASE_URL=http://localhost:8000/api
VITE_KAKAO_MAP_KEY=                                # [1차 8단계] 카카오 JavaScript 키
VITE_TOSS_CLIENT_KEY=                              # [1차 7단계] 토스 테스트 클라이언트 키 (브라우저 노출용)
VITE_PAYMENT_MODE=                                 # 비우면 데모 결제(바로 완료), toss 면 토스 테스트 결제창
```

> 지금 `.env.example` 에는 `HIRA_SERVICE_KEY` 로 되어 있습니다. 약국 API 를 붙이는 8단계에서 `DATA_GO_KR_SERVICE_KEY` 로 이름을 바꾸고, 토스 키는 7단계에서 추가합니다.

## 11. 배포와 데모 운영

| 대상 | 방법 |
|---|---|
| 프론트 | Vercel, `frontend/` 루트. SPA rewrite 설정. 토스 성공·실패 URL 을 배포 주소로 |
| 백엔드 | Render, 시작 명령 `python -m alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| DB | Aiven for MySQL, `DATABASE_URL` 을 Render 환경 변수에 등록 (SSL 접속 옵션) |

- Render 무료 서버는 잠들어서 첫 요청이 느림 → 시작 화면에서 `/api/health` 로 미리 깨움
- Aiven 무료 MySQL 은 오래 안 쓰면 꺼질 수 있음 → 지원 기간에는 주기적으로 확인
- 데모 초기화(A-5): `python -m scripts.seed --reset` 을 매일 실행 (GitHub Actions)

## 12. 테스트

**[1차] 꼭 확인할 것**
- 권한: 게스트 예약 → 401, 의사가 예약 → 403, 남의 예약 조회 → 404, 심사 중 의사 진료 시작 → 403
- **동시 예약**: 같은 슬롯에 두 요청을 동시에 보내면 하나만 201, 하나는 409 (실제 MariaDB/MySQL 에서, `test_mysql.py`)
- 취소 후 같은 슬롯 다시 예약 가능
- 슬롯 계산: 점심시간·지난 시간·휴진 요일 제외, 한국 자정 전후 날짜 경계
- 상태 전이: `booked` 가 아닌 예약 취소 → 409, `in_progress` 가 아닌 진료 완료 → 409
- 진료 완료 트랜잭션: 처방 항목 저장 중 실패하면 예약 상태도 그대로 (롤백)
- 초진 7일 제한, 초진·재진 판정, 나이대별 진료비
- 결제: 금액 불일치 → 400 이고 토스 호출 안 함 (토스 클라이언트는 테스트에서 가짜로 교체), 같은 confirm 두 번 → 한 번만 처리
- 결제 전 처방전 → 403, 약국 두 번 전송 → 409, 배송인데 사유 없음 → 400

**이미 있는 테스트**: 앱 실행·에러 형식·JWT·비밀번호·DB 설정 (`test_setup.py`, `test_config.py`), 실제 DB 한글·UTC·유니크 (`test_mysql.py`)

## 13. 이후 개선 후보

- [보류] 화상통화: idea.md 12. 보류한 화상통화 메모
- 알림 polling → SSE (F-4)
- 진료 시간표 편집, 휴진일 등록
- refresh token + httpOnly 쿠키
- 의사 파트너 플랜 (X-1)
- GitHub Actions 로 MariaDB·MySQL 두 DB 에서 테스트 자동 실행
- 검색 개선: MVP 는 `LIKE`. 한글 전문 검색은 MySQL(ngram)과 MariaDB(Mroonga) 방식이 달라 배포 DB 기준으로 결정
