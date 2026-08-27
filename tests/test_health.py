from fastapi.testclient import TestClient
from app.main import app

def test_health_check_is_public() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_unknown_private_path_requires_token() -> None:
    response = TestClient(app).get("/private")
    assert response.status_code == 401
    assert response.json() == {"detail": "Bearer token required"}
