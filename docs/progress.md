# 진행 기록

## 2026-10-26 Phase 2·3 완료

### 완료한 것

- **Phase 2: 사용자 모델과 첫 데이터베이스**
  - SQLAlchemy로 DB 연결 (`backend/app/core/database.py`), 개발 DB는 `database/buildlog.sqlite3`
  - 사용자 모델: 이메일·닉네임 중복 금지, Argon2 비밀번호 암호화, 운영자 여부(기본 아님)
  - Alembic 첫 마이그레이션(`204b404e2459`)을 개발 DB에 적용
  - 자동 테스트는 매번 새 임시 SQLite에서 실행
- **Phase 3: 회원가입·로그인·닉네임 변경**
  - API: `POST /api/auth/signup`, `POST /api/auth/login`, `GET /api/auth/me`, `PATCH /api/account/nickname`
  - 로그인 토큰은 `HttpOnly`, `SameSite=Lax` 쿠키로 전달 (1일 유지)
  - 화면: 회원가입, 로그인, 내 기록 홈, 계정 설정. 로그인하지 않으면 로그인 화면으로 이동
- 테스트: 백엔드 73개, 프론트엔드 9개 통과. 실제 서버로 가입→로그인→닉네임 변경→서버 재시작 후 데이터 유지 확인

### 구현하면서 정한 것

- 이메일은 앞뒤 공백만 지우고 대소문자를 구분해 저장·비교합니다. `User@Example.com`과 `user@example.com`은 다른 계정입니다. (사용자 요청으로 변경)
- 닉네임의 한글은 완성된 글자(가~힣)만 허용합니다. `ㄱㄴ` 같은 자음·모음만으로는 만들 수 없습니다.
- 닉네임은 대소문자를 구분합니다. `Abc`와 `abc`는 서로 다른 닉네임입니다.
- 이메일·비밀번호가 틀렸을 때는 어느 쪽이 틀렸는지 알려주지 않습니다.

### 다음 할 일

- 사용자 확인: 브라우저에서 회원가입·로그인·닉네임 변경 직접 확인
- Phase 4: 공부 기록·할 일·오류 기록의 데이터 구조

## 2026-10-26 회원 기능 수정

### 완료한 것

- 이메일 대소문자 구분: 가입·로그인 모두 입력한 그대로 비교 (spec 2.1에 규칙 추가)
- 로그아웃 추가: `POST /api/auth/logout`이 로그인 쿠키를 지우고, 머리글에 로그아웃 버튼 추가 (spec 2.4 추가)
- 테스트: 백엔드 77개, 프론트엔드 11개 통과. 실제 서버에서 대소문자 구분과 로그아웃 후 접근 차단 확인

### 다음 할 일

- 사용자 확인: 브라우저에서 로그아웃 버튼 직접 확인
- Phase 4: 공부 기록·할 일·오류 기록의 데이터 구조

## 2026-10-26 Supabase(PostgreSQL) 연결 준비 (plan Phase 13 일부를 앞당김)

### 완료한 것

- 백엔드 설정을 `backend/.env`에서 읽도록 변경 (기존 최상위 `.env`를 `backend/.env`로 옮김, `SECRET_KEY` 유지)
- `DATABASE_URL`을 필수로 변경. 비어 있거나 잘못되면 SQLite로 넘어가지 않고 확인할 내용을 안내하며 멈춤
- Supabase가 주는 `postgresql://` 주소를 psycopg 드라이버 주소로 자동 변환, SSL 필수, 연결 대기 10초 제한
- 오류 안내와 로그에 비밀번호·전체 연결 주소가 나오지 않게 처리
- `psycopg[binary]==3.3.6` 설치
- 두 번째 마이그레이션(`6606785c14da`): PostgreSQL에서 `users` 테이블에 RLS(행 단위 보안) 켜기. Supabase 공개 키로 테이블을 읽지 못하게 함
- 연결 확인 명령 추가: `backend`에서 `.venv\Scripts\python -m app.scripts.check_db`
- `backend/.env.example`에 Session pooler 주소 넣는 방법 설명. 최상위 `.env.example`은 삭제
- 테스트: 백엔드 91개 통과 (자동 테스트는 계속 임시 SQLite 사용)
- 기존 `database/buildlog.sqlite3`는 삭제하지 않음. 데이터 이전은 하지 않음

### 확인하지 못한 것

- 실제 Supabase 연결과 테이블 생성: 연결 정보가 아직 입력되지 않음

### 다음 할 일

- 사용자: `backend/.env`에 `DATABASE_URL` 입력 → `check_db` → `alembic upgrade head` → 서버 재시작 후 회원가입·로그인 확인
- 이후 새 테이블을 만들 때마다 PostgreSQL에서 RLS를 켜는 마이그레이션을 함께 작성
- Phase 4: 공부 기록·할 일·오류 기록의 데이터 구조
