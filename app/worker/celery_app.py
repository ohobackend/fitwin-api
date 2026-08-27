from celery import Celery
from app.core.config import get_settings

settings = get_settings()
celery_app = Celery(
    "fitwin", broker=settings.celery_broker_url, backend=settings.celery_result_backend,
    include=["app.worker.tasks.garments", "app.worker.tasks.fitting_2d"],
)
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=86400,
    timezone="Asia/Seoul",
    enable_utc=True,
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=settings.celery_task_eager_propagates,
    task_store_eager_result=True,
)
