from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.schemas.error import ErrorResponse

COMMON_ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Bad request"},
    401: {"model": ErrorResponse, "description": "Authentication required"},
    403: {"model": ErrorResponse, "description": "Permission denied"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    413: {"model": ErrorResponse, "description": "Payload too large"},
    415: {"model": ErrorResponse, "description": "Unsupported media type"},
    422: {"model": ErrorResponse, "description": "Validation or quality check failed"},
    500: {"model": ErrorResponse, "description": "Internal server error"},
    503: {"model": ErrorResponse, "description": "Dependent service unavailable"},
}

def install_openapi(app: FastAPI) -> None:
    def custom_openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(title=app.title, version="0.1.0", routes=app.routes)
        security_schemes = schema.setdefault("components", {}).setdefault("securitySchemes", {})
        security_schemes["BearerAuth"] = {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
        for path, operations in schema.get("paths", {}).items():
            for method, operation in operations.items():
                if method.lower() in {"get", "post", "put", "patch", "delete"} and path != "/health":
                    operation["security"] = [{"BearerAuth": []}]
        app.openapi_schema = schema
        return schema
    app.openapi = custom_openapi
