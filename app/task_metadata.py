"""Transient request metadata used by the task-status response."""

from datetime import datetime


_task_metadata: dict[str, dict[str, str | datetime]] = {}


def record_task_upload(task_id: str, original_filename: str, upload_time: datetime) -> None:
    """Associate upload-only metadata with a queued task without altering its payload."""
    _task_metadata[task_id] = {
        "original_filename": original_filename,
        "upload_time": upload_time,
    }


def get_task_upload_metadata(task_id: str) -> dict[str, str | datetime]:
    """Return upload metadata when it is available in this API process."""
    return _task_metadata.get(task_id, {})
