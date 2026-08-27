from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.middleware.jwt_auth import JWTAuthMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.app_name, lifespan=lifespan)
    application.add_middleware(
        JWTAuthMiddleware,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    application.include_router(api_router)
    return application


app = create_app()

