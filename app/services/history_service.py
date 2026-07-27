"""Prediction history persistence and retrieval service."""

from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models import PredictionHistory


def create_prediction_history(
    db: Session,
    data: Dict[str, Any],
) -> PredictionHistory:
    """Save one fully completed final recommendation."""
    try:
        prediction_history = PredictionHistory(**data)
        db.add(prediction_history)
        db.commit()
        db.refresh(prediction_history)
        return prediction_history
    except Exception as exc:
        db.rollback()
        raise RuntimeError(f"Failed to save prediction history: {str(exc)}") from exc


def get_prediction_history(
    db: Session,
    user_id: int,
) -> List[PredictionHistory]:
    """Return a user's prediction history from newest to oldest."""
    return (
        db.query(PredictionHistory)
        .filter(PredictionHistory.user_id == user_id)
        .order_by(PredictionHistory.created_at.desc())
        .all()
    )


def get_prediction_history_by_id(
    db: Session,
    user_id: int,
    history_id: int,
) -> PredictionHistory | None:
    """Return one prediction only when it belongs to the requesting user."""
    return (
        db.query(PredictionHistory)
        .filter(
            PredictionHistory.id == history_id,
            PredictionHistory.user_id == user_id,
        )
        .first()
    )
