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
