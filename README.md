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
