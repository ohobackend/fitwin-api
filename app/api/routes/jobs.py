from typing import Any
from celery.result import AsyncResult
from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from app.schemas.job import JobResponse, JobStatus
from app.worker.celery_app import celery_app

router = APIRouter(prefix="/jobs", tags=["jobs"])
STATE_MAP: dict[str, JobStatus] = {
    "PENDING": "pending",
    "RECEIVED": "processing",
    "STARTED": "processing",
    "RETRY": "retrying",
    "SUCCESS": "done",
    "FAILURE": "failed",
    "REVOKED": "failed",
}

def read_job(job_id: str) -> JobResponse:
    task: AsyncResult = celery_app.AsyncResult(job_id)
    state = task.state
    result: dict[str, Any] | None = None
    error: str | None = None
    if state == "SUCCESS" and isinstance(task.result, dict):
        result = task.result
    elif state in {"FAILURE", "REVOKED"}:
        error = "Task failed"
    return JobResponse(job_id=job_id, status=STATE_MAP.get(state, "pending"), result=result, error=error)

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str) -> JobResponse:
    return await run_in_threadpool(read_job, job_id)
