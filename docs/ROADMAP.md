# Deployment Quality Roadmap

이 문서는 Tunnel Smart Advisor를 **로컬 프로토타입**에서 **배포 가능한 엔지니어링 SaaS 품질**로 올리기 위한 실행 로드맵이다. 로컬 실행 절차는 `docs/RUNBOOK.md`, 저장소 구조는 `docs/STRUCTURE.md`, UI 기준은 `docs/design.md`를 참조하고 여기서는 중복 설명하지 않는다.

## 현재 기준 상태

### 강점

- `backend/`: FastAPI 라우터와 서비스 계층이 분리되어 있다.
- `frontend/`: React + Vite + TypeScript 기반이며 TanStack Query API 계층이 있다.
- `data/tunnel_checklist/`: 백엔드가 직접 사용하는 CSV 온톨로지와 관계 그래프 데이터가 정리되어 있다.
- `docs/design.md`: 사이드바, 카드, 표, 위험 배지 등 제품 UI 기준이 명확하다.
- `docs/RUNBOOK.md`: 로컬 실행, 포트, 기본 헬스체크가 정리되어 있다.

### 배포 전 핵심 리스크

| 영역 | 현재 문제 | 배포 리스크 |
| --- | --- | --- |
| 의존성 | `requirements.txt`, `frontend/package.json`이 버전 고정 없이 최신 버전을 사용 | 재설치 시 다른 결과가 나올 수 있음 |
| 설정 | 데이터 경로, CORS, API URL이 개발 환경 중심 | staging/production 전환이 어려움 |
| 보안 | `backend/main.py`의 CORS가 전체 origin 허용 | 외부 사이트에서 API 호출 가능 |
| 테스트 | pytest/Vitest 회귀 테스트가 구축됨 | 신규 기능 추가 시 테스트 누락 가능 |
| CI/CD | `.github/workflows/ci.yml`이 backend/frontend/data smoke 검증 실행 | 배포 자동화는 별도 운영 절차 필요 |
| 배포 | non-Docker 서버 실행 및 정적 파일 제공 절차 문서화 | reverse proxy 실제 서버 설정은 환경별 적용 필요 |
| 관측성 | 구조화 로그, readiness check, metrics 구현됨 | 장기 보관/대시보드는 별도 운영 도구 필요 |
| 데이터 운영 | CSV schema 검증과 `load_data()` smoke 검증 구축 | 백업/버전 정책은 운영 프로세스로 관리 필요 |

## 목표 품질 기준

배포 가능 상태는 아래 조건을 모두 만족해야 한다.

- 새 환경에서 README/RUNBOOK만 보고 설치와 실행이 가능하다.
- backend/frontend 의존성이 lock/pin 되어 동일 버전으로 재현된다.
- pull request마다 backend syntax, unit tests, frontend typecheck/build가 자동 실행된다.
- production CORS, API URL, 데이터 디렉터리, 로그 레벨이 환경 변수로 제어된다.
- `/health`와 별도로 데이터 로딩까지 검증하는 readiness endpoint가 있다.
- 명시적 서버 배포 절차로 backend/frontend가 실행 가능하다.
- 위험도 산정, 그래프 생성, 주요 API에 대한 회귀 테스트가 있다.
- 실제 데이터가 없는 기능은 명확히 비활성/empty state로 표시하고 mock을 배포하지 않는다.

## Phase 0: 기준선 안정화 (즉시)

### 0.1 의존성 고정

**목표:** 개발자별 설치 결과를 동일하게 만든다.

- [x] `requirements.txt`의 패키지 버전을 고정한다.
  - 예: `fastapi==...`, `uvicorn[standard]==...`, `pandas==...`, `openpyxl==...`, `pypdf==...`
- [x] `frontend/package.json`의 `latest` 의존성을 실제 설치 버전으로 고정한다.
- [x] `npm install --prefix frontend`로 `frontend/package-lock.json`을 생성하고 커밋한다.
- [x] README의 설치 섹션에 lockfile 기준 설치 명령을 명시한다.

**검증:**

```powershell
pip install -r requirements.txt
npm ci --prefix frontend
python -m compileall -q backend scripts scratch
npm run build --prefix frontend
```

### 0.2 환경 변수 기준 정리

**목표:** 개발/운영 설정을 코드 수정 없이 바꿀 수 있게 한다.

- [x] `.env.example` 추가
  - `TUNNEL_DATA_DIR=data/tunnel_checklist`
  - `TUNNEL_CORS_ORIGINS=http://127.0.0.1:2000`
  - `TUNNEL_LOG_LEVEL=INFO`
  - `VITE_API_BASE_URL=http://127.0.0.1:8080`
- [x] `backend/config.py`가 `os.getenv()` 또는 Pydantic settings 기반으로 데이터 경로를 읽게 한다.
- [x] `frontend/src/api/client.ts`의 fallback URL은 유지하되 배포 문서에서 `VITE_API_BASE_URL` 설정을 필수로 안내한다.

### 0.3 배포 mock 차단 원칙 확정

**목표:** mock 데이터가 실제 운영 화면에 섞이지 않게 한다.

- [x] 실제 API가 없는 화면은 현재처럼 empty state를 유지한다.
- [x] mock이 필요한 개발용 데이터는 `frontend/src/mocks/`로 분리하고 파일명에 `mock`을 명시한다.
- [x] production build에서 mock import가 남아 있는지 검색하는 CI step을 추가한다.

## Phase 1: 테스트 기반 확보

### 1.1 Backend unit tests

**우선 테스트 대상:**

- `backend/services/risk_scoring.py`
  - 조건 선택이 risk score에 반영되는지
  - 자연어 query 매칭이 score를 증가시키는지
  - risk level percentile 분류가 의도대로 동작하는지
- `backend/services/graph_builder.py`
  - graph JSON이 `nodes`, `edges`를 반환하는지
  - 최상위 위험에 전략 노드가 연결되는지
- `backend/routers/nodes.py`
  - 지원 node type은 200
  - 미지원 node type은 404
- `backend/routers/score.py`
  - 빈 조건은 빈 결과 또는 의도된 기본 결과 반환
  - 정상 조건은 `ScoreResponse` shape 반환

**추가 파일:**

- `tests/backend/test_risk_scoring.py`
- `tests/backend/test_graph_builder.py`
- `tests/backend/test_nodes_api.py`
- `tests/backend/test_score_api.py`
- `pytest.ini` 또는 `pyproject.toml`

**검증 명령:**

```powershell
pytest tests/backend -q
```

### 1.2 Frontend regression tests

**우선 테스트 대상:**

- API client error handling
- `Workspace`가 `/score/` 응답을 받아 risk cards와 graph panel을 렌더링하는지
- `Dashboard`가 `/dashboard/summary` 응답을 렌더링하는지
- `Library`가 `/library/items` 응답을 렌더링하고 검색/카테고리 필터가 작동하는지

**권장 도구:** Vitest + React Testing Library + MSW

**추가 파일:**

- `frontend/src/api/client.test.ts`
- `frontend/src/pages/Workspace.test.tsx`
- `frontend/src/pages/Dashboard.test.tsx`
- `frontend/src/pages/Library.test.tsx`

## Phase 2: CI/CD 도입

### 2.1 Pull request CI

**목표:** main branch에 깨진 코드가 들어오지 않게 한다.

**추가 파일:** `.github/workflows/ci.yml`

필수 job:

1. Backend
   - Python setup
   - `pip install -r requirements.txt`
   - `python -m compileall -q backend scripts scratch`
   - `pytest tests/backend -q`
2. Frontend
   - Node setup
   - `npm ci --prefix frontend`
   - `npm run build --prefix frontend`
3. Data smoke
    - 필수 CSV 파일 존재 확인
    - `backend.services.data_loader.load_data()` 호출 확인 (`python scripts/tools/smoke_load_data.py`)

### 2.2 릴리즈 기준

배포 tag를 만들기 전 아래 항목을 통과해야 한다.

- [x] backend tests pass
- [x] frontend build pass
- [x] non-Docker backend/frontend deployment checks pass
- [x] `/health`와 `/health/ready` pass
- [x] production 환경 변수 누락 없음
- [x] mock 데이터 production import 없음

## Phase 3: 보안/설정 hardening

### 3.1 CORS 제한

**현재:** `backend/main.py`에서 `allow_origins=["*"]`.

**목표:** production에서는 명시된 frontend origin만 허용한다.

- [x] `TUNNEL_CORS_ORIGINS` 환경 변수 추가
- [x] 쉼표 구분 origin 목록 파싱
- [x] dev 기본값은 `http://127.0.0.1:2000`
- [x] production 기본값은 없음; 누락 시 startup fail 고려

### 3.2 입력 검증

`backend/routers/score.py`의 `ScoreRequest`에 검증을 추가한다.

- [x] `query` 최대 길이 제한
- [x] dropdown field 최대 길이 제한
- [x] 빈 문자열 normalization
- [x] 잘못된 type에 대한 422 응답 확인 테스트

### 3.3 API 보호 정책

초기 내부 도구라면 최소한 아래 중 하나를 선택한다.

- 사내망/VPN 안에서만 접근
- reverse proxy Basic Auth
- 사내망/서버 경계 기반 접근 제어
- 추후 JWT/session auth

## Phase 4: 데이터 운영 품질

### 4.1 CSV schema 검증

**목표:** 잘못된 CSV가 런타임 중 500 오류로 터지지 않게 한다.

검증 대상:

- `nodes_ground.csv`: `id:ID`, `condition_name`, `:LABEL`
- `nodes_method.csv`: `id:ID`, `method_name`, `:LABEL`
- `nodes_equipment.csv`: `id:ID`, `equip_name`, `:LABEL`
- `nodes_risk.csv`: `id:ID`, `description`, `source_project`, `:LABEL`
- `nodes_strategy.csv`: `id:ID`, `action`, `source_project`, `:LABEL`
- `rels_total.csv`: `:START_ID`, `:END_ID`, `:TYPE`

**추가 스크립트:** `scripts/tools/validate_ontology.py`

검증 항목:

- 필수 컬럼 존재
- `id:ID` 중복 없음
- relationship endpoint가 실제 node id를 참조하는지
- 빈 description/action 없음

### 4.2 데이터 갱신 절차

`scripts/ontology/build_master_ontology.py` 실행 이후 아래 절차를 표준화한다.

1. ontology build 실행
2. schema validation 실행
3. data load smoke 실행
4. backend unit tests 실행
5. API smoke test 실행
6. 변경 CSV diff 검토
7. 배포 artifact 생성

### 4.3 캐시 정책

현재 `backend/services/data_loader.py`는 `@lru_cache(maxsize=1)`로 CSV를 영구 캐시한다.

- [x] 운영에서는 배포 시 backend restart를 표준 절차로 둔다.
- [x] cache reload endpoint 또는 파일 mtime 기반 reload를 검토한다. (`POST /admin/cache/reload` 구현, 사내망/서버 경계로 접근 제한)

## Phase 5: 관측성/운영성

### 5.1 Health endpoints

현재 `/health`는 shallow check다. 아래 endpoint를 추가한다.

- `/health`: 프로세스 alive
- `/health/ready`: CSV 파일 존재, `load_data()` 성공, 핵심 row count 확인

예상 ready 응답:

```json
{
  "status": "ready",
  "data": {
    "risk": 316,
    "strategy": 316,
    "rels": 1219
  }
}
```

### 5.2 Structured logging

- [x] backend startup 로그: data dir, loaded row counts, CORS origins
- [x] `/score/` 요청 로그: request id, selected filters, result count, latency
- [x] 예외 로그: traceback + request id

### 5.3 Metrics

초기에는 로그 기반으로 충분하지만, 서버 운영을 시작하면 아래를 추가한다.

- [x] request count
- [x] request latency
- [x] error count
- [x] score endpoint latency percentile
- [x] data load failure count

## Phase 6: 배포 단위 만들기

### 6.1 명시적 서버 배포 구성

목표:

- backend process: FastAPI + uvicorn 실행 명령 문서화
- frontend artifact: Vite build 결과(`frontend/dist/`)를 정적 서버로 제공
- data directory: `data/tunnel_checklist/`와 `TUNNEL_DB_PATH`를 호스트 경로로 명시

### 6.2 Reverse proxy

권장 구조:

```text
Internet
  -> HTTPS reverse proxy
  -> /        frontend static files
  -> /api/*   FastAPI backend
```

필수 고려:

- HTTPS termination
- gzip/brotli
- request body size limit
- CORS 최소화
- cache headers for static assets

### 6.3 배포 환경 분리

최소 2개 환경을 둔다.

- `staging`: 데이터 업데이트 및 UI 검수
- `production`: 사용자 접근 환경

환경별로 달라져야 할 값:

- API URL
- CORS origins
- 데이터 디렉터리/볼륨
- 로그 레벨
- 인증 정책

## Phase 7: 제품 기능 완성도

현재 `Workspace`, `Dashboard`, `Library`는 실제 백엔드 데이터와 연결되어 있지만, 아래 기능은 데이터 원천이 없다.

### 7.1 분석 이력

필요한 백엔드 기능:

- [x] 분석 요청 저장 (`/score/`가 SQLite 저장 후 `history_id` 반환)
- [x] 분석 결과 snapshot 저장 (`result_json` 저장)
- [x] 검색어 기반 조회 (`GET /history/analyses?query=`)
- [x] 프로젝트/기간 기반 조회 (`project`, `date_from`, `date_to` query parameter)
- [x] 재실행 (`POST /history/analyses/{history_id}/rerun`)

권장 저장소:

- 초기: SQLite (`TUNNEL_DB_PATH`, 기본 `data/runtime/tunnel_history.sqlite3`)
- 협업/운영: PostgreSQL

### 7.2 리포트

필요한 백엔드 기능:

- [x] 분석 결과 기반 HTML 리포트 생성 (`GET /reports/{history_id}.html`)
- [x] 리포트 목록 조회 (`GET /reports`)
- [x] 다운로드/열람 (`download_url` 기반 HTML 열기)
- [x] PDF 리포트 생성 (`GET /reports/{history_id}.pdf`)
- [x] 공유 상태 관리 (`POST /reports/{history_id}/share`)

### 7.3 알림

필요한 백엔드 기능:

- [x] 데이터 갱신 알림 (초기 운영 알림 seed)
- [x] 분석 완료 알림 (`/score/` 완료 시 생성)
- [x] 시스템 점검 알림 (초기 시스템 알림 seed)
- [x] 읽음/중요 상태 저장 (`/notifications/*` SQLite API)

## 권장 실행 순서

| 순서 | 작업 | 예상 효과 |
| ---: | --- | --- |
| 1 | 의존성 버전 고정 + lockfile | 재현 가능한 설치 |
| 2 | `.env.example` + backend config env화 | 환경 분리 가능 |
| 3 | backend pytest 최소 세트 | 핵심 위험도 엔진 보호 |
| 4 | GitHub Actions CI | main branch 품질 게이트 |
| 5 | CORS 제한 + 입력 검증 | 기본 보안 수준 확보 |
| 6 | CSV schema validator | 데이터 변경 사고 방지 |
| 7 | `/health/ready` + structured logging | 운영 장애 추적 가능 |
| 8 | 명시적 서버 배포 + reverse proxy | 반복 가능한 배포 |
| 9 | 분석 이력/리포트/알림 저장소 | 제품 기능 완성 |

## Definition of Done: 배포 가능 판정

아래 체크리스트를 모두 만족하면 “내부 사용자 대상 배포 가능”으로 본다.

- [x] `npm ci --prefix frontend`와 `pip install -r requirements.txt`가 항상 같은 버전을 설치한다.
- [x] `python -m compileall -q backend scripts scratch` 통과
- [x] `pytest tests/backend -q` 통과
- [x] `npm run build --prefix frontend` 통과
- [x] CI가 PR마다 위 검증을 자동 실행
- [x] production CORS origin이 명시적으로 제한됨
- [x] `.env.example`이 있고 production secret/config는 git에 없음
- [x] `/health/ready`가 데이터 로딩까지 검증
- [x] CSV schema validator가 배포 전 실행됨
- [x] 명시적 서버 배포 절차가 문서화됨
- [x] mock 데이터가 production 화면에 노출되지 않음

## 관련 문서

- `README.md`: 프로젝트 개요, 설치, 로컬 실행, 기본 검증 명령
- `docs/RUNBOOK.md`: 로컬 운영 절차와 troubleshooting
- `docs/STRUCTURE.md`: 저장소 구조
- `docs/design.md`: UI/UX 디자인 시스템
