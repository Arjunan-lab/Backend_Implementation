"""Soil health score API routes."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.models import User
from app.routes.crop_routes import CropPredictionRequest
from app.services.soil_health_score_service import predict_soil_health_score

router = APIRouter()


@router.post("/soil-health-score", tags=["Soil Health Score"])
async def predict_soil_health_score_endpoint(
    request: CropPredictionRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Predict a numeric soil health score from soil and environmental features."""
    try:
        result = predict_soil_health_score(request.dict())
        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=f"Model files not found: {str(exc)}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(exc)}") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(exc)}") from exc
