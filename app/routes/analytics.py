"""Authenticated analytics API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import User
from app.schemas import AnalyticsResponse
from app.services.analytics_service import get_user_analytics


router = APIRouter(tags=["Analytics"])


@router.get(
    "/analytics",
    summary="Get personal analytics",
    description=(
        "Return prediction, crop recommendation, uploaded image, and history totals, "
        "plus the latest prediction timestamp and most frequently predicted soil type "
        "in the user's preferred language, "
        "for the authenticated user only."
    ),
    response_model=AnalyticsResponse,
    responses={
        401: {"description": "Authentication failed."},
        500: {"description": "Analytics could not be retrieved."},
    },
)
def get_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalyticsResponse:
    """Return analytics scoped to the logged-in user."""
    try:
        return AnalyticsResponse(
            **get_user_analytics(db, current_user.id, current_user.language_id)
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve analytics.",
        ) from exc
