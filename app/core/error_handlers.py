import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

def error_content(status_code: int, message: str, detail=None) -> dict:
    return {"status_code": status_code, "message": message, "detail": detail}

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        if isinstance(exc.detail, str):
            message, detail = exc.detail, None
        elif isinstance(exc.detail, dict):
            message = str(exc.detail.get("message", "Request failed"))
            detail = {key: value for key, value in exc.detail.items() if key != "message"} or None
        else:
            message, detail = "Request failed", exc.detail
        return JSONResponse(error_content(exc.status_code, message, detail), exc.status_code, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = []
        for item in exc.errors():
            safe = {key: value for key, value in item.items() if key not in {"input", "ctx"}}
            safe["location"] = list(safe.pop("loc", ()))
            errors.append(safe)
        return JSONResponse(error_content(422, "Request validation failed", errors), 422)

    @app.exception_handler(Exception)
    async def internal_error(_: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled API error", exc_info=(type(exc), exc, exc.__traceback__))
        return JSONResponse(error_content(500, "Internal server error"), 500)
