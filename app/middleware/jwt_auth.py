import jwt
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from app.core.security import decode_access_token
from app.core.error_handlers import error_content

PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

class JWTAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret_key: str, algorithm: str) -> None:
        super().__init__(app)
        self.secret_key = secret_key
        self.algorithm = algorithm

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)
        scheme, _, token = request.headers.get("Authorization", "").partition(" ")
        if scheme.lower() != "bearer" or not token:
            return JSONResponse(status_code=401, content=error_content(401, "Bearer token required"))
        try:
            request.state.user = decode_access_token(token, self.secret_key, self.algorithm)
        except jwt.ExpiredSignatureError:
            return JSONResponse(status_code=401, content=error_content(401, "Token has expired"))
        except jwt.InvalidTokenError:
            return JSONResponse(status_code=401, content=error_content(401, "Invalid token"))
        return await call_next(request)
