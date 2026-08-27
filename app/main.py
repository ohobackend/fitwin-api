from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.error_handlers import register_exception_handlers
from app.core.openapi import COMMON_ERROR_RESPONSES, install_openapi
from app.middleware.jwt_auth import JWTAuthMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name, version="0.1.0", lifespan=lifespan,
        responses=COMMON_ERROR_RESPONSES,
    )
    application.add_middleware(
        JWTAuthMiddleware,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    application.include_router(api_router)
    register_exception_handlers(application)
    install_openapi(application)
    return application


app = create_app()

