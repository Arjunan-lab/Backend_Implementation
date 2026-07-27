"""Analytics queries for authenticated users."""

from collections import Counter
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import PredictionHistory
from app.services.sarvam_service import translate_text


def get_user_analytics(
    db: Session, user_id: int, language_id: int | None = None
) -> dict[str, int | str | datetime | None]:
    """Return prediction totals and summary details for one user."""
    total_predictions = (
        db.query(PredictionHistory)
        .filter(PredictionHistory.user_id == user_id)
        .count()
    )
    total_image_uploads = (
        db.query(PredictionHistory)
        .filter(
            PredictionHistory.user_id == user_id,
            PredictionHistory.soil_image_path.isnot(None),
        )
        .count()
    )
    prediction_history = (
        db.query(PredictionHistory)
        .filter(PredictionHistory.user_id == user_id)
        .all()
    )
    total_crop_recommendations = sum(
        len(history.recommended_crops or []) for history in prediction_history
    )
    last_prediction = max(
        (history.created_at for history in prediction_history),
        default=None,
    )
    soil_counts = Counter(history.soil_type for history in prediction_history)
    most_predicted_soil = (
        soil_counts.most_common(1)[0][0] if soil_counts else None
    )
    translated_most_predicted_soil = (
        translate_text(most_predicted_soil, language_id)
        if most_predicted_soil is not None
        else None
    )

    return {
        "total_predictions": total_predictions,
        "total_crop_recommendations": total_crop_recommendations,
        "total_image_uploads": total_image_uploads,
        "prediction_history": total_predictions,
        "last_prediction": last_prediction,
        "most_predicted_soil": translated_most_predicted_soil,
    }
