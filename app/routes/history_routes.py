"""Prediction history API routes."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import PredictionHistory, User
from app.schemas import PredictionHistoryDetailResponse, PredictionHistorySummaryResponse
from app.services.history_service import get_prediction_history, get_prediction_history_by_id


router = APIRouter(tags=["Prediction History"])


from app.services.sarvam_service import translate_text


def _get_top_crop(recommended_crops: list[Any], language_id: int | None) -> str | None:
    """Return the first crop from the stored crop recommendations."""
    if not recommended_crops:
        return None

    top_crop = recommended_crops[0]
    raw_name = top_crop.get("crop") if isinstance(top_crop, dict) else str(top_crop)
    return translate_text(raw_name, language_id) if raw_name else None


def _serialize_detail(prediction: PredictionHistory, language_id: int | None) -> Dict[str, Any]:
    """Build the complete saved prediction response translated to preferred language."""
    def translate_item(item: Any) -> Any:
        if isinstance(item, dict):
            return {k: translate_text(v, language_id) if isinstance(v, str) else v for k, v in item.items()}
        if isinstance(item, str):
            return translate_text(item, language_id)
        return item

    return {
        "history_id": prediction.id,
        "prediction_date": prediction.created_at,
        "soil_type": translate_text(prediction.soil_type, language_id),
        "soil_confidence": prediction.soil_confidence,
        "nitrogen": prediction.nitrogen,
        "phosphorus": prediction.phosphorus,
        "potassium": prediction.potassium,
        "ph": prediction.ph,
        "organic_carbon": prediction.organic_carbon,
        "electrical_conductivity": prediction.electrical_conductivity,
        "temperature": prediction.temperature,
        "humidity": prediction.humidity,
        "soil_health": translate_text(prediction.soil_health, language_id),
        "soil_health_score": prediction.soil_health_score,
        "soil_fertility_status": translate_text(prediction.soil_fertility_status, language_id),
        "deficiencies": [translate_item(d) for d in (prediction.nutrient_deficiencies or [])],
        "recommended_crops": [translate_item(c) for c in (prediction.recommended_crops or [])],
        "recommended_fertilizers": [translate_item(f) for f in (prediction.recommended_fertilizers or [])],
    }


@router.get("/history", response_model=List[PredictionHistorySummaryResponse])
def list_prediction_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return lightweight history summaries for the logged-in user."""
    predictions = get_prediction_history(db, current_user.id)
    return [
        {
            "history_id": prediction.id,
            "id": prediction.user_id,
            "prediction_date": prediction.created_at,
            "soil_type": translate_text(prediction.soil_type, current_user.language_id),
            "soil_health": translate_text(prediction.soil_health, current_user.language_id),
            "soil_health_score": prediction.soil_health_score,
            "soil_fertility_status": translate_text(prediction.soil_fertility_status, current_user.language_id),
            "top_crop": _get_top_crop(prediction.recommended_crops, current_user.language_id),
        }
        for prediction in predictions
    ]


@router.get("/history/{history_id}", response_model=PredictionHistoryDetailResponse)
def get_prediction_history_detail(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Return one complete saved prediction."""
    is_admin = (current_user.role == "admin")
    prediction = get_prediction_history_by_id(db, current_user.id, history_id, is_admin=is_admin)
    if prediction is None:
        raise HTTPException(
            status_code=404,
            detail=f"Prediction history with ID '{history_id}' not found for user '{current_user.email}'.",
        )

    return _serialize_detail(prediction, current_user.language_id)

