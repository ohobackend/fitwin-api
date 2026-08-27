import logging
from uuid import UUID
from celery.signals import task_failure
from app.db.sync_session import SyncSessionFactory
from app.models.job_failure_log import JobFailureLog

logger = logging.getLogger(__name__)
ENTITY_TYPES = {
    "garments.process": "garment",
    "fitting.process_2d": "fitting_result",
    "assets.generate_3d": "asset_3d",
}

@task_failure.connect
def record_task_failure(sender=None, task_id=None, exception=None, args=None, einfo=None, **_) -> None:
    task_name = getattr(sender, "name", "unknown")
    entity_id = None
    if args:
        try:
            entity_id = UUID(str(args[0]))
        except (TypeError, ValueError):
            pass
    try:
        with SyncSessionFactory() as session:
            session.add(JobFailureLog(
                task_id=str(task_id), task_name=task_name,
                entity_type=ENTITY_TYPES.get(task_name), entity_id=entity_id,
                error_type=type(exception).__name__, error_message=str(exception)[:4000],
                traceback=str(einfo)[:20000] if einfo else None,
                retry_count=int(getattr(getattr(sender, "request", None), "retries", 0)),
            ))
            session.commit()
    except Exception:
        logger.exception("Could not persist Celery failure for task %s", task_id)
