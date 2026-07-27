"""Image prediction API routes for soil classification."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.dependencies import get_current_user
from app.models import User
from app.services.image_service import predict_soil


router = APIRouter()

_UPLOADS_DIR = Path(__file__).resolve().parents[1] / "uploads"
_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/predict-image", tags=["Prediction"])
async def predict_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Accept an uploaded soil image and return a prediction payload."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    if file.content_type not in {"image/jpeg", "image/png", "image/jpg", "image/webp"}:
        raise HTTPException(status_code=400, detail="Invalid image file type.")

    temp_file_path = None
    try:
        temp_file_path = _UPLOADS_DIR / f"{file.filename}"
        with temp_file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = predict_soil(str(temp_file_path), current_user.language_id)
        return {
            "soil_type": result["soil_type"],
            "confidence": result["confidence"],
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Image file not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if temp_file_path and temp_file_path.exists():
            temp_file_path.unlink(missing_ok=True)
