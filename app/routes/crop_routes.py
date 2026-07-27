"""Crop recommendation API routes."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import get_current_user
from app.models import User
from app.services.crop_service import recommend_crop

router = APIRouter()


class CropPredictionRequest(BaseModel):
    """Request model for crop recommendation."""

    soil_type: str = Field(..., description="Type of soil (e.g., 'Clayey', 'Sandy', 'Loamy')")
    nitrogen: float = Field(..., ge=0, description="Nitrogen content (N) in kg/ha")
    phosphorus: float = Field(..., ge=0, description="Phosphorus content (P) in kg/ha")
    potassium: float = Field(..., ge=0, description="Potassium content (K) in kg/ha")
    ph: float = Field(..., ge=0, le=14, description="Soil pH value (0-14)")
    organic_carbon: float = Field(..., description="Organic carbon content")
    electrical_conductivity: float = Field(..., description="Electrical conductivity")
    temperature: float = Field(..., ge=-50, le=60, description="Temperature in Celsius")
    humidity: float = Field(..., ge=0, le=100, description="Humidity percentage (0-100)")


@router.post("/predict-crop", tags=["Crop Recommendation"])
async def predict_crop(
    request: CropPredictionRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Recommend a crop based on soil and environmental conditions.

    Takes soil properties and environmental factors as input and returns
    a crop recommendation suitable for those conditions.

    Args:
        request: CropPredictionRequest containing:
            - soil_type: Type of soil
            - nitrogen: Nitrogen content (N) in kg/ha
            - phosphorus: Phosphorus content (P) in kg/ha
            - potassium: Potassium content (K) in kg/ha
            - ph: Soil pH value (0-14)
            - organic_carbon: Organic carbon content
            - electrical_conductivity: Electrical conductivity
            - temperature: Temperature in Celsius
            - humidity: Humidity percentage (0-100)

    Returns:
        JSON response with recommended crop:
        {
            "recommended_crop": "Rice"
        }

    Raises:
        HTTPException: If prediction fails or required files are missing.
    """
    try:
        request_data = request.dict()
        result = recommend_crop(request_data, current_user.language_id)
        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=f"Model files not found: {str(exc)}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(exc)}") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(exc)}") from exc
