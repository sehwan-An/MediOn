# MediON

의사 찾기 → 예약 → 진료(상태 변경) → 결제(토스 테스트) → 처방전 → 약국 선택 → 약 수령까지 이어지는 비대면진료 앱.
질문·답변(Q&A)은 2차 부가 기능, 화상통화는 보류.
**포트폴리오용 데모 프로젝트**이며 실제 서비스로 배포하지 않는다. 모든 사용자·의사·약·진료 데이터는 가상이다.

## 문서

작업 전에 관련 문서를 먼저 확인한다.

- 기획, 범위, 비목표: `docs/idea.md`
- 기능 목록과 ID(A-1, I-3 …), 완료 기준, 개발 순서: `docs/requirements.md`
- 아키텍처, DB, API, 권한, 디자인 토큰: `docs/tech-spec.md`

문서와 다르게 구현해야 할 이유가 생기면 먼저 말하고, 합의되면 문서도 함께 고친다.

## 기술 스택

- **frontend/**: React + Vite + React Router, **JavaScript (TypeScript 사용 안 함)**, Tailwind CSS v4, TanStack Query + axios, 카카오맵 JS SDK, 토스페이먼츠 결제위젯 SDK
- **backend/**: FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, MariaDB 11.4(개발)·MySQL 8(배포) (PyMySQL), JWT (PyJWT)
- 새 라이브러리를 추가하기 전에 **먼저 물어본다.**

## 명령어

```bash
# frontend
cd frontend
npm install
npm run dev            # http://localhost:5173
npm run build
npm run lint

# backend
cd backend
python -m venv .venv
.venv\Scripts\activate           # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python -m alembic upgrade head
python -m scripts.seed           # 시드 데이터 입력 (--reset: 초기화)
python -m uvicorn app.main:app --reload   # http://localhost:8000/docs
python -m pytest  # TEST_DATABASE_URL 을 설정하면 MySQL 테스트까지 실행
```

## 작업 방식

- 코드를 수정할 때는 부분 diff가 아니라 **수정된 파일 전체**를 보여준다.
- git 브랜치나 PR은 **요청할 때만** 만든다.
- 한 번에 requirements.md의 기능 ID 단위로 작업하고, 끝나면 어떤 ID를 완료했는지 알려준다.
- 설명과 주석은 한국어로 쓴다. 변수·함수·파일 이름은 영어로 쓴다.
- 터미널 명령어를 안내할 때는 맨 위에 **🐍 가상환경 필요**(backend, `.venv\Scripts\activate` 후 실행) 또는 **가상환경 불필요**(frontend, HeidiSQL 등)를 반드시 표시한다.
- 개발 환경은 Windows (명령 프롬프트·PowerShell) 이다.
- 가상환경 안의 실행 파일(`pytest.exe`, `uvicorn.exe` 등)은 PC 보안 정책(Device Guard)에 막힐 수 있다. 항상 `python -m pytest`, `python -m uvicorn`, `python -m alembic` 처럼 `python -m` 으로 안내한다.

## 프론트엔드 규칙

- 폴더: 화면은 `src/pages/[섹션]/`, 공통 컴포넌트는 `src/components/`, API 호출은 `src/api/`에만 둔다.
- 컴포넌트는 함수형, 파일 이름은 PascalCase (`QuestionCard.jsx`).
- 컴포넌트 안에서 axios를 직접 부르지 않는다. `src/api/`의 함수를 TanStack Query로 감싸서 쓴다.
- 모든 데이터 화면은 **로딩 / 에러 / 빈 상태**를 처리한다.
- 진료과 목록은 `src/constants/departments.js`만 사용한다 (백엔드 코드와 일치).

### Tailwind 규칙

- 색·폰트는 `src/index.css`의 `@theme` 토큰만 쓴다 (`bg-primary`, `text-ink-muted`). **임의 색상값(`bg-[#123456]`) 금지.**
- 환자 화면 주요 색은 `primary`, 의사 화면은 `doctor`.
- 상태 색은 대기·진행 중 `wait` / 완료 `done` 을 쓴다 (예약됨, 결제 대기, 조제 중, 답변 대기 등). 빨강·초록은 쓰지 않는다.
- 클래스가 길어지거나 같은 조합이 3번 이상 반복되면 `components/ui/`의 컴포넌트로 뺀다. `@apply`는 쓰지 않는다.
- 상태에 따라 클래스를 바꿀 때는 삼항 연산자로 처리하고, 조건이 많아지면 컴포넌트 안에 객체로 정리한다.
- 모바일 우선. 기준 너비 390px, 터치 영역 최소 44px (`min-h-11`).
- 아이콘만 있는 버튼에는 `aria-label`, 클릭 요소는 `<button>`이나 `<a>`만 쓴다 (`div`에 onClick 금지).

## 백엔드 규칙

- `routers/`는 요청·응답과 권한 의존성(`require_role`)만, 판단 로직은 `services/`에 둔다.
- 요청·응답은 항상 Pydantic 스키마(`schemas/`)를 거친다. 모델을 그대로 반환하지 않는다.
- 권한 검사는 반드시 백엔드에서 한다. 프론트 라우트 보호는 화면 편의용이다.
- 다른 사람의 예약·결제·처방전(2차: 비공개 질문)은 403이 아니라 **404**로 응답한다.
- 에러는 `{ "error": { "code", "message" } }` 형식, `message`는 사용자에게 바로 보여줄 한국어 문장.
- 여러 테이블을 바꾸는 작업(진료 완료 = 예약 상태 변경 + 처방전 저장 + 결제 요청 생성 + 알림)은 하나의 트랜잭션으로 처리한다.
- 예약·결제·약 수령 상태는 requirements.md의 상태 흐름 순서로만 바꾼다. 맞지 않는 상태에서 요청하면 409.
- 중복 예약 방지는 "조회 후 저장"이 아니라 DB 유니크 제약(`appointments.slot_key`)으로 최종 판정한다.
- 결제 금액은 브라우저가 보낸 값을 믿지 않고 서버에 저장한 금액으로 검증한다.
- 진료 시간표·"오늘" 계산은 한국 시간(`Asia/Seoul`)으로 하고, 저장은 UTC로 한다.
- DB 스키마를 바꾸면 Alembic 마이그레이션을 함께 만든다.
- 날짜·시간 컬럼은 `app.db.types.UTCDateTime`을 쓴다. DB에는 UTC로 저장하고, 한국 시간 변환은 화면에서 한다.
- MySQL 마이그레이션의 downgrade에서 외래 키가 쓰는 인덱스를 따로 지우지 않는다 (MySQL error 1553). 테이블을 지우면 같이 지워진다.
- DB는 `utf8mb4`(한글·이모지)로 만든다.
- `alembic.ini`에는 한글을 쓰지 않는다. 한국어 Windows에서 Alembic이 이 파일을 cp949로 읽어서 `UnicodeDecodeError`가 난다.
- 개발(MariaDB)과 배포(MySQL) DB가 다르므로 **둘 다 지원하는 기능만 쓴다.** 한쪽에만 있는 기능(MySQL ngram 파서, MariaDB 전용 문법 등)은 쓰기 전에 먼저 물어본다.
- 외부 API(토스, 약국 정보, 2차 심평원)는 `services/*_client.py`에서만 호출하고, 타임아웃을 적용한다. 공공데이터는 캐시한다.

## 보안·환경 변수

- 비밀 값은 `.env`에만 두고 커밋하지 않는다. 새 변수를 추가하면 `.env.example`도 고친다.
- 토스 시크릿 키와 공공데이터 API 키는 백엔드에만 둔다. 프론트에 노출되는 키는 카카오맵 JavaScript 키와 토스 **클라이언트** 키뿐이다.
- 결제는 토스페이먼츠 **테스트 키**만 쓴다. 라이브 키(`live_`)는 넣지 않는다.
- 의사 인증 서류는 공개 URL로 저장하거나 노출하지 않는다. 관리자만 단기 링크로 열람한다.
- 앱 화면에 "체험하기" 같은 데모 전용 진입점을 만들지 않는다. 시연용 계정은 README에만 적는다.

## 의료 데모 데이터 원칙

- 모든 화면에 "포트폴리오용 데모" 배너를 유지한다.
- 의사·병원 이름은 실존 인물, 실제 병원, 드라마 캐릭터를 쓰지 않고 새로 지은 이름을 쓴다.
- 처방전에 쓰는 약은 시드 `drugs` 목록에서만 고른다. 처방전 화면의 **"데모 처방전" 워터마크**를 지우지 않는다.
- 시드 진료 요약과 (2차) 의사 답변은 일반적인 안내 수준으로 쓰고, 구체적인 진단명처럼 읽히지 않게 한다.
- (2차) 질문 상세 화면의 "진단·처방을 대신하지 않음" 안내 문구를 지우지 않는다.
- 약국 전송·약 배송은 실제로 일어나지 않는다는 점을 화면에 표시한다 ("데모: 다음 단계로" 버튼 등).
- AI로 의료 답변을 생성하는 기능은 만들지 않는다.
