# MediON

> 의사를 찾아 예약하고, 비대면으로 진료받고, 결제 후 처방전을 받아 가까운 약국에서 약을 받는 비대면진료 앱

**포트폴리오용 데모 프로젝트입니다.** 실제 의료 서비스가 아니며, 모든 사용자·의사·약·진료 데이터는 가상입니다. 결제는 기본이 **데모 결제**(누르면 바로 완료)이고, 토스페이먼츠 테스트 결제창으로도 바꿀 수 있습니다. 실제 돈은 나가지 않습니다.

## 주요 기능

- **로그인 없이 시작하기**: 의사 목록·상세는 바로 둘러보기, 예약할 때 로그인
- **의사 찾기**: 증상 카테고리 → 맞는 진료과 의사, 오늘 가능 여부·재진 희망률
- **예약**: 진료 시간표에서 30분 단위 선택, **같은 시간 중복 예약 방지** (DB 유니크 제약 + 동시성 테스트)
- **진료**: 의사가 진료 시작 → 진료 완료 (진료 요약 + 처방전 작성). 화상통화는 보류
- **결제**: 데모 결제(기본) / 토스페이먼츠 테스트 결제(`VITE_PAYMENT_MODE=toss`), **서버에 저장된 금액으로 승인 검증**
- **처방전 · 약국**: 결제 후 처방전 열람("데모 처방전"), 근처 약국 선택(카카오맵 + 공공데이터), 방문 수령 / 대상자만 배송
- **진행 단계**: 예약 → 진료 → 결제 → 처방전 → 약 수령을 예약 상세 하나에서 확인
- **의사 면허 인증**: 서류 제출 → 심사 중 → 관리자 승인/반려 (서류는 공개 주소 없이 관리자만 열람)
- **알림 · 후기**: 예약·진료·결제·약 수령 알림, 진료 후기와 재진 희망률
- **오늘 약 복용**: 약을 받은 처방전으로 홈에 아침·점심·저녁 복용표, 먹었어요 체크
- **질문·답변**: 증상 질문 → 의사 답변(대면 진료 권유) → 도움돼요 → "이 의사에게 진료 받기"로 예약까지 연결

## 시연용 계정

`python -m scripts.seed` 를 실행하면 아래 계정이 만들어집니다. 비밀번호는 모두 `medion1234` 입니다. 모든 이름·병원은 가상입니다.

| 역할 | 이메일 | 메모 |
|---|---|---|
| 환자 | `jiwoo@demo.medion` | 한지우 · 30대 직장인 |
| 환자 | `minjae@demo.medion` | 최민재 · 부모님 건강을 챙기는 보호자 |
| 의사 (인증 완료) | `doyoon@demo.medion` | 김도윤 · 내과 · 가온내과의원 (그 외 인증 의사 9명은 `scripts/seed.py` 참고) |
| 의사 (심사 중) | `hyunwoo@demo.medion` | 이현우 · 정형외과 · 심사 중 화면 확인용 |
| 관리자 | `admin@demo.medion` | 의사 인증 심사 (이현우의 데모 서류로 승인/반려 시연) |

시드에는 시연용 환자 두 명의 **지난 진료 12건**(완료·데모 결제·후기)도 들어 있어서 의사 목록·상세에서 재진 희망률과 후기를 바로 볼 수 있습니다. 한지우 계정에는 **복용 중인 처방**(홈 오늘 약 복용 카드)이, 상담 탭에는 **질문 11개**(답변 대기 3개 포함)가 들어 있습니다.

결제하기를 누르면 바로 결제 완료됩니다(데모 결제). 토스 테스트 결제창을 보려면 `frontend/.env` 에 `VITE_PAYMENT_MODE=toss` 를 넣고 프론트 서버를 다시 켜세요.

## 기술 스택

| 영역 | 사용 기술 |
|---|---|
| Frontend | React, Vite, React Router, Tailwind CSS v4, TanStack Query, axios, 카카오맵 SDK, 토스페이먼츠 결제창 |
| Backend | FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, PyJWT, bcrypt, httpx |
| DB | MariaDB 11.4 (개발) · MySQL 8 (배포) |
| 외부 데이터 | 토스페이먼츠 (테스트), 공공데이터포털 약국 정보 |

## 폴더 구조

```
MediOn/
├── CLAUDE.md        # AI 작업 규칙
├── docs/            # 기획·기능 명세·기술 설계
├── frontend/        # React 앱
└── backend/         # FastAPI 서버
```

## 실행 방법

### 준비물

- Node.js 20 이상
- Python 3.11 이상
- MariaDB 11.4 또는 MySQL 8 + HeidiSQL 같은 DB 관리 도구

### DB 만들기 (HeidiSQL)

HeidiSQL로 로컬 MariaDB(또는 MySQL)에 접속한 뒤 쿼리 탭에서 실행합니다. 한글이 깨지지 않게 꼭 `utf8mb4`로 만들어주세요.

```sql
CREATE DATABASE IF NOT EXISTS medion CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- 테스트 전용 DB (선택)
CREATE DATABASE IF NOT EXISTS medion_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

`backend/.env`에는 HeidiSQL 접속 정보와 같은 값을 한 줄씩 적어요. 파일 안의 **"✏️ 직접 입력"** 표시가 있는 줄만 채우면 돼요.

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=내_비밀번호      # 특수문자가 있어도 그대로
DB_NAME=medion
JWT_SECRET=긴_랜덤_문자열
```

### 백엔드

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env          # macOS/Linux: cp .env.example .env
# .env 의 "✏️ 직접 입력" 줄(DB_PASSWORD, JWT_SECRET) 채우기

python -m alembic upgrade head
python -m scripts.seed
python -m uvicorn app.main:app --reload   # http://localhost:8000/docs
```

테스트:

```bash
python -m pytest  # 기본 테스트 (MySQL 테스트는 건너뜀)

# MySQL 테스트까지 (Windows PowerShell, medion_test DB 필요)
$env:TEST_DATABASE_URL="mysql+pymysql://root:your_password@localhost:3306/medion_test?charset=utf8mb4"
python -m pytest
```

### 프론트엔드

```bash
cd frontend
npm install
copy .env.example .env          # macOS/Linux: cp .env.example .env
npm run dev                     # http://localhost:5173
```

## 문서

- [기획서](docs/idea.md): 왜 만들었는지, 페르소나, 기능별 구현 수준, 제도·규제 고려, 결정 기록
- [기능 명세](docs/requirements.md): 기능 ID, 우선순위, 완료 기준, 상태 흐름, 화면 목록, 개발 순서
- [기술 설계](docs/tech-spec.md): 아키텍처, DB, API, 권한, 핵심 로직(중복 예약·결제 승인), 디자인 토큰

## 앞으로 할 것

- 배포 (Vercel · Render · Aiven MySQL)
- 근처 병원 찾기, 가족 대신 예약, 의사 진료 취소
- 화상통화는 보류
