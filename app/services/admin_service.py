"""Business service layer for administrative functions."""

from typing import Any, Dict, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models import ChatHistory, PredictionHistory, User, UserRole
from app.schemas import UserRoleUpdateRequest


def get_all_users(
    db: Session,
    skip: int = 0,
    limit: int = 50,
) -> List[User]:
    """Retrieve paginated user list for admin management."""
    return (
        db.query(User)
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def find_user_strictly(db: Session, identifier: str) -> User | None:
    """Find a user account strictly by ID (numeric), email (@ format), or exact username."""
    from sqlalchemy import func
    clean_id = str(identifier).strip()
    if not clean_id:
        return None

    # 1. Exact Numeric ID match (e.g. 45)
    if clean_id.isdigit():
        user = db.query(User).filter(User.id == int(clean_id)).first()
        if user:
            return user

    # 2. Exact Email match (e.g. john@example.com)
    if "@" in clean_id:
        user = db.query(User).filter(func.lower(User.email) == clean_id.lower()).first()
        if user:
            return user

    # 3. Exact Username match in database
    user = db.query(User).filter(User.username == clean_id).first()
    if user:
        return user

    return None


def update_user_role(
    db: Session,
    target_identifier: str,
    role_data: UserRoleUpdateRequest,
    current_admin_id: int,
) -> User:
    """Update a specified user's security role strictly by ID, email, or username."""
    # Priority: URL path target_identifier (e.g. 45 or john@example.com) takes highest precedence
    search_target = target_identifier.strip() if target_identifier else (role_data.username or "").strip()

    user = find_user_strictly(db, search_target)
    if not user and role_data.username:
        user = find_user_strictly(db, role_data.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with identifier '{search_target}' not found in database.",
        )

    # Prevent admin from demoting themselves to avoid lockouts
    if user.id == current_admin_id and role_data.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot demote their own account.",
        )

    new_role = role_data.role.value if hasattr(role_data.role, "value") else str(role_data.role)
    user.role = new_role

    # Preserve user.username exactly as stored in DB
    db.commit()
    db.refresh(user)
    return user


def update_user_status(
    db: Session,
    target_identifier: str,
    status_data: Any,
    current_admin_id: int,
) -> User:
    """Update a user's account status (strictly by username, email, or ID)."""
    user = find_user_strictly(db, str(target_identifier))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User account '{target_identifier}' not found in database.",
        )

    if user.id == current_admin_id and status_data.status == "suspended":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot suspend their own account.",
        )

    new_status = status_data.status.value if hasattr(status_data.status, "value") else str(status_data.status)
    user.status = new_status
    db.commit()
    db.refresh(user)
    return user


def delete_user_account(
    db: Session,
    target_identifier: str,
    current_admin_id: int,
) -> None:
    """Delete a user account and associated cascade data (strictly by username, email, or ID)."""
    user = find_user_strictly(db, str(target_identifier))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User account '{target_identifier}' not found in database.",
        )

    if user.id == current_admin_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot delete their own account.",
        )

    db.delete(user)
    db.commit()


def get_system_analytics(db: Session) -> Dict[str, Any]:
    """Calculate system-wide statistics across all users."""
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import func

    total_users = db.query(User).count()
    total_farmers = db.query(User).filter(User.role == "farmer").count()
    total_admins = db.query(User).filter(User.role == "admin").count()
    active_users = db.query(User).filter(User.status == "active").count()
    suspended_users = db.query(User).filter(User.status == "suspended").count()

    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    recent_farmers_count = (
        db.query(User)
        .filter(User.role == "farmer", User.created_at >= thirty_days_ago)
        .count()
    )

    total_predictions = db.query(PredictionHistory).count()
    total_chat_messages = db.query(ChatHistory).count()

    # Regional breakdown query
    region_rows = (
        db.query(User.region, func.count(User.id))
        .group_by(User.region)
        .all()
    )
    users_by_region = {
        (r[0] if r[0] else "Unspecified"): r[1]
        for r in region_rows
    }

    return {
        "total_users": total_users,
        "total_farmers": total_farmers,
        "total_admins": total_admins,
        "active_users": active_users,
        "suspended_users": suspended_users,
        "recent_farmers_count": recent_farmers_count,
        "total_predictions": total_predictions,
        "total_chat_messages": total_chat_messages,
        "users_by_region": users_by_region,
    }
