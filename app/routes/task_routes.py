"""Task status API routes."""

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException

from app.celery_app import celery_app
from app.schemas import TaskStatusResponse
from app.task_metadata import get_task_upload_metadata


router = APIRouter()


@router.get("/tasks/{task_id}", tags=["Tasks"], response_model=TaskStatusResponse)
def get_task_status(task_id: str) -> TaskStatusResponse:
    """Return task information only; prediction output is not exposed here."""
    try:
        result = AsyncResult(task_id, app=celery_app)
        metadata = get_task_upload_metadata(task_id)

        return TaskStatusResponse(
            task_id=task_id,
            status=result.status,
            original_filename=metadata.get("original_filename"),
            upload_time=metadata.get("upload_time"),
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
