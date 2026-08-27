# FitTwin 백엔드 개발 명세서

## 프로젝트 개요
FitTwin은 실물 의류 이미지를 AI로 2D/3D 디지털 패션 콘텐츠로 변환하고,
모바일/PC/HMD 환경에서 가상 피팅과 구매 전환을 지원하는 XR 커머스 서비스입니다.
이 문서는 백엔드(AI 서버 + API 서버) 구현 범위를 정의합니다.

## 기술 스택
- **API 서버**: Python 3.11+, FastAPI
- **비동기 작업 큐**: Celery + Redis (또는 RQ)
- **DB**: PostgreSQL
- **파일 저장소**: Object Storage (S3 호환, 예: AWS S3 / MinIO)
- **AI 모델**:
  - 배경 제거 / 의류 영역 분할: rembg 또는 SAM(Segment Anything) 계열 오픈소스
  - 2D 가상 피팅: OOTDiffusion 계열
  - 3D 생성: TRELLIS 또는 LRM 계열, GLB 포맷 변환
- **인증**: JWT 기반 간단 인증 (개인 MVP 수준)

## 개발 순서 (Codex에게 이 순서대로 단계별 요청)

### 1단계 — DB 스키마 & 기본 API 서버 골격
- FastAPI 프로젝트 초기 구조 생성 (라우터, 설정, DB 연결 분리)
- PostgreSQL 테이블 설계
  - `users`: id, email, created_at
  - `garments`: id, user_id, original_image_url, category, color, status, created_at
  - `fitting_results`: id, garment_id, user_id, result_type(2d/3d), result_url, created_at
  - `assets_3d`: id, garment_id, glb_url, thumbnail_url, status, created_at
- Object Storage 업로드/다운로드 유틸 함수 구현
- 간단한 JWT 인증 미들웨어 구현
- 헬스체크 엔드포인트 (`GET /health`)

### 2단계 — 의류 이미지 업로드 & 전처리 API
- `POST /garments/upload`: 이미지 업로드 → Object Storage 저장 → DB 레코드 생성
- 배경 제거/영역 분할 모델 연동 (rembg 등)
- 카테고리/색상 자동 분류 로직 연동 → DB 저장
- 처리 상태 필드(`status`: uploaded → processing → done/failed) 관리

### 3단계 — 비동기 작업 큐 구축
- Celery + Redis 설정 (워커 프로세스 분리)
- AI 추론 작업은 모두 큐를 통해 비동기 실행되도록 구조화
- `GET /jobs/{job_id}`: 작업 상태 조회 API (pending/processing/done/failed)
- 실패 시 재시도 로직 (최대 재시도 횟수 설정)

### 4단계 — 2D 가상 피팅 모델 연동 (OOTDiffusion)
- OOTDiffusion 오픈소스 추론 코드를 워커에 통합
- `POST /fitting/2d`: garment_id + 기본 모델(또는 아바타) 이미지 → 큐에 작업 등록
- 결과 이미지 Object Storage 저장 + `fitting_results` 테이블 기록
- 결과 캐싱 (동일 조합 재요청 시 캐시 반환)

### 5단계 — 3D 자산 생성 모델 연동 (TRELLIS/LRM)
- TRELLIS 또는 LRM 계열 모델을 별도 GPU 워커로 분리 (무거운 작업이므로 큐 우선순위 분리 권장)
- 메시/텍스처 생성 → GLB 포맷 변환 파이프라인 구현
- `POST /assets/3d/generate`: garment_id → 큐에 작업 등록
- `GET /assets/3d/{garment_id}`: GLB URL 및 상태 조회
- 결과물을 Three.js/WebXR에서 바로 로드 가능한 형태로 검증

### 6단계 — 구매 전환 연동 API
- `GET /products/{id}/link`: 상품 상세 페이지 링크 반환
- `GET /products/{id}/qr`: QR 코드 생성 API
- `POST /cart/add`: 장바구니 이동(연동) 엔드포인트 (실제 결제 없이 목데이터 수준도 가능)

### 7단계 — 품질 검수 & 에러 처리
- 생성 결과 품질 필터링 로직 (예: 빈 이미지, 깨진 GLB 감지)
- 실패한 작업 로그 기록 및 관리자용 조회 API
- 전체 API 에러 응답 포맷 통일 (status code, message, detail)

## API 명세 우선 확정 권장 사항
프론트엔드와 병행 개발을 위해 1단계 완료 직후 아래 항목을 **OpenAPI(Swagger) 문서로 먼저 확정**할 것을 권장합니다.
- 업로드 요청/응답 스키마
- 작업 상태 조회 응답 스키마
- 2D/3D 결과 응답 스키마 (더미 데이터 포함)

## 참고 — MVP 우선순위
- **필수(1차 MVP)**: 1~4단계, 6단계 일부(링크/QR)
- **핵심 차별화(2차)**: 5단계(3D 자산 생성)
- **확장 기능(범위 외)**: 관리자 페이지, 대량 상품 등록 API
