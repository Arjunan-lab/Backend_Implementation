"""Soil health API routes."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import get_current_user
from app.models import User
from app.services.soil_health_service import predict_soil_health


router = APIRouter()


class SoilHealthRequest(BaseModel):
    """Request model for soil health prediction."""

    soil_type: str = Field(..., description="Type of soil (e.g., 'Clayey', 'Sandy', 'Loamy')")
    nitrogen: float = Field(..., ge=0, description="Nitrogen content (N) in kg/ha")
    phosphorus: float = Field(..., ge=0, description="Phosphorus content (P) in kg/ha")
    potassium: float = Field(..., ge=0, description="Potassium content (K) in kg/ha")
    ph: float = Field(..., ge=0, le=14, description="Soil pH value (0-14)")
    organic_carbon: float = Field(..., description="Organic carbon content")
    electrical_conductivity: float = Field(..., description="Electrical conductivity")
    temperature: float = Field(..., ge=-50, le=60, description="Temperature in Celsius")
    humidity: float = Field(..., ge=0, le=100, description="Humidity percentage (0-100)")


@router.post("/soil-health", tags=["Soil Health"])
async def predict_soil_health_status(
    request: SoilHealthRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Predict soil health based on soil and environmental conditions."""
    try:
        request_data = request.dict()
        result = predict_soil_health(request_data, current_user.language_id)
        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=f"Model files not found: {str(exc)}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(exc)}") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(exc)}") from exc
