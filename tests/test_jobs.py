from app.api.routes.jobs import STATE_MAP

def test_celery_states_are_mapped_to_api_states() -> None:
    assert STATE_MAP["PENDING"] == "pending"
    assert STATE_MAP["STARTED"] == "processing"
    assert STATE_MAP["RETRY"] == "retrying"
    assert STATE_MAP["SUCCESS"] == "done"
    assert STATE_MAP["FAILURE"] == "failed"

def test_garment_task_retries_at_most_three_times() -> None:
    from app.worker.tasks.garments import process_garment
    assert process_garment.max_retries == 3
