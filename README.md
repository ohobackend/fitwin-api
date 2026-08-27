# FitTwin API

FitTwin XR 패션 커머스의 FastAPI 백엔드입니다. 현재는 개발 명세의 1단계인
PostgreSQL 스키마, 기본 서버 구조, JWT 인증 미들웨어와 S3 호환 스토리지
유틸리티까지만 구현되어 있습니다.

## 실행

```bash
cp .env.example .env
docker compose up -d db minio
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

서버 상태는 `GET /health`, API 문서는 `/docs`에서 확인할 수 있습니다.
`/health`와 문서 경로를 제외한 API는 `Authorization: Bearer <JWT>` 헤더가
필요합니다.

## 테스트

```bash
pytest
```

## 의류 이미지 업로드

`POST /garments/upload`에 JPEG 또는 PNG 파일을 multipart의 `file` 필드로
전송합니다. JWT의 `sub`에는 DB에 존재하는 사용자 UUID가 들어가야 합니다.
원본과 `rembg` 처리 결과는 Object Storage에 저장되며, 파일명 기반 카테고리와
전경의 대표 색상이 DB에 기록됩니다. 처리 상태는
`uploaded → processing → done`으로 바뀌고 오류 발생 시 `failed`로 보존됩니다.

## 비동기 워커

Redis와 Celery 워커를 실행한 뒤 API 서버를 시작합니다.

```bash
docker compose up -d db minio redis worker
uvicorn app.main:app --reload
```

의류 업로드는 `202 Accepted`와 `job_id`를 즉시 반환합니다. 처리 상태는
`GET /jobs/{job_id}`에서 `pending`, `processing`, `retrying`, `done`, `failed`로
조회할 수 있습니다. 전처리 실패 작업은 1초, 2초, 4초 간격으로 최대 3회
재시도됩니다.

## 2D 가상 피팅

GPU 워커 환경은 공식 OOTDiffusion 코드 및 가중치와 분리되어 있습니다.

```bash
bash scripts/install_ootdiffusion.sh
bash scripts/run_gpu_worker.sh
```

설치 스크립트는 공식 GitHub 저장소, `levihsu/OOTDiffusion` 체크포인트와
`openai/clip-vit-large-patch14`를 내려받습니다. 공식 구현과 마찬가지로 Linux,
CUDA 11.8 환경을 기준으로 합니다. 모델 라이선스는 비상업적 사용 제한이 있는
CC BY-NC-SA 4.0이므로 실제 서비스 적용 전에 반드시 확인해야 합니다.

`POST /fitting/2d`는 multipart 요청을 받습니다.

```bash
curl -X POST http://localhost:8000/fitting/2d \
  -H "Authorization: Bearer <JWT>" \
  -F "garment_id=<GARMENT_UUID>" \
  -F "model_image=@person.jpg"
```

카테고리는 의류 DB 값으로 자동 매핑하며 필요하면 `category=upperbody|lowerbody|dress`와
`model_type=hd|dc`를 명시할 수 있습니다. 캐시 미스는 `202`와 `job_id`, 완료된 동일
조합은 `200`과 기존 `result_url`을 반환합니다.

## TRELLIS 3D 자산 생성

TRELLIS는 2D 피팅 워커와 분리된 `gpu_3d` 큐에서 동작합니다.

```bash
alembic upgrade head
bash scripts/install_trellis.sh
bash scripts/run_trellis_worker.sh
```

`POST /assets/3d/generate`에 `{"garment_id":"<UUID>"}`를 전송하면 작업을
등록하고, `GET /assets/3d/{garment_id}`에서 상태와 `glb_url`을 조회할 수 있습니다.
완료된 자산의 중복 생성 요청은 기존 결과를 즉시 반환합니다.

생성된 GLB는 업로드 전 glTF 2.0 구조와 렌더링 가능한 mesh를 검사합니다. 실제
Three.js 로더 호환성은 다음 명령으로 추가 검증할 수 있습니다.

```bash
cd tests/threejs
npm install
npm run validate -- /path/to/generated.glb
```

## 품질 검수와 실패 로그

업로드 및 AI 결과 이미지는 디코딩 가능 여부, 크기, 픽셀 수, 시각 정보와 투명
전경을 검사합니다. GLB는 헤더, chunk 경계, glTF 2.0, mesh POSITION accessor와
내장 buffer 길이를 검사한 후에만 Object Storage에 저장됩니다.

최종 재시도까지 실패한 Celery 작업은 `job_failure_logs`에 기록됩니다. 관리자
JWT에 `role: "admin"` 또는 `is_admin: true` claim을 넣어 조회할 수 있습니다.

```bash
curl http://localhost:8000/admin/failures?limit=50 \
  -H "Authorization: Bearer <ADMIN_JWT>"
```

모든 API 오류는 다음 형식을 사용합니다.

```json
{"status_code": 422, "message": "Request validation failed", "detail": []}
```

프론트엔드 전달용 명세는 루트의 `openapi.json`이며 코드 변경 후 다음 명령으로
다시 생성할 수 있습니다.

```bash
python scripts/export_openapi.py
```

## 구매 전환 API

현재 커머스 연동은 목 구현이며 `PRODUCT_STORE_BASE_URL`을 실제 쇼핑몰 주소로
교체할 수 있습니다.

- `GET /products/{id}/link`: 상품 상세 링크 JSON 반환
- `GET /products/{id}/qr`: 상품 링크를 담은 PNG QR 코드 반환
- `POST /cart/add`: 인증 사용자 기준 목 장바구니 항목 반환

```json
{
  "product_id": "sku-100",
  "quantity": 1,
  "garment_id": null
}
```
