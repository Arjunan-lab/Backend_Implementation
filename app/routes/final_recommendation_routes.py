"""Final recommendation API routes."""

import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.dependencies import get_current_user
from app.models import User
from app.schemas import FinalRecommendationResponse
from app.task_metadata import record_task_upload
from app.tasks.final_recommendation_task import generate_final_recommendation


router = APIRouter()

_UPLOADS_DIR = Path(__file__).resolve().parents[1] / "uploads"
_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


@router.post(
    "/final-recommendation",
    tags=["Final Recommendation"],
    response_model=FinalRecommendationResponse,
)
async def get_final_recommendation(
    image: UploadFile = File(...),
    nitrogen: float = Form(...),
    phosphorus: float = Form(...),
    potassium: float = Form(...),
    ph: float = Form(...),
    organic_carbon: float = Form(...),
    electrical_conductivity: float = Form(...),
    temperature: float = Form(...),
    humidity: float = Form(...),
    current_user: User = Depends(get_current_user),
) -> FinalRecommendationResponse:
    """Queue a recommendation and return its completed prediction fields."""
    if not image.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    if image.content_type not in {"image/jpeg", "image/png", "image/jpg", "image/webp"}:
        raise HTTPException(status_code=400, detail="Invalid image file type.")

    try:
        suffix = Path(image.filename).suffix
        with tempfile.NamedTemporaryFile(
            dir=_UPLOADS_DIR,
            suffix=suffix,
            delete=False,
        ) as buffer:
            temp_file_path = Path(buffer.name)
            shutil.copyfileobj(image.file, buffer)

        task = generate_final_recommendation.delay(
            str(temp_file_path),
            nitrogen,
            phosphorus,
            potassium,
            ph,
            organic_carbon,
            electrical_conductivity,
            temperature,
            humidity,
            current_user.language_id,
            current_user.id,
        )
        record_task_upload(task.id, image.filename, datetime.now(timezone.utc))
        recommendation = await run_in_threadpool(task.get)

        response_data = {
            key: value
            for key, value in recommendation.items()
            if key != "soil_confidence"
        }
        return FinalRecommendationResponse(task_id=task.id, **response_data)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Image file not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
