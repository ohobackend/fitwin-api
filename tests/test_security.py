from app.core.security import create_access_token, decode_access_token

def test_access_token_round_trip() -> None:
    token = create_access_token("user-1")
    payload = decode_access_token(token, "change-me-in-production", "HS256")
    assert payload["sub"] == "user-1"
