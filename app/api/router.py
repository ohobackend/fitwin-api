from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.garments import router as garments_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.fitting import router as fitting_router
from app.api.routes.assets_3d import router as assets_3d_router
from app.api.routes.commerce import router as commerce_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(garments_router)
api_router.include_router(jobs_router)
api_router.include_router(fitting_router)
api_router.include_router(assets_3d_router)
api_router.include_router(commerce_router)
