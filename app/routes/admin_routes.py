from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import authenticate_user, register_user
from app.dependencies import get_current_admin_user, get_db
from app.models import User, UserRole
from app.schemas import (
    AdminSystemAnalyticsResponse,
    AdminUserSummaryResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserRegisterResponse,
    UserResponse,
    UserRoleUpdateRequest,
    UserRoleUpdateResponse,
    UserStatusUpdateRequest,
    UserStatusUpdateResponse,
)
from app.services.admin_service import (
    delete_user_account,
    get_all_users,
    get_system_analytics,
    update_user_role,
    update_user_status,
)
from app.utils import create_access_token, create_refresh_token

router = APIRouter(prefix="/admin", tags=["Admin Management"])


@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Admin Registration Endpoint",
    description="Registers an Administrator account with required username, role ('admin'), region, and admin_secret validation.",
)
def admin_register(
    user_data: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    """Register an administrator account with strict admin_secret validation."""
    user_data.role = UserRole.ADMIN
    user = register_user(db, user_data)
    return {"message": f"Administrator account '{user.email}' created successfully."}


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Admin Login Endpoint",
    description="Authenticates admin credentials specifically. Standard farmer accounts are denied access with HTTP 403 Forbidden.",
)
def admin_login(
    login_data: UserLoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate administrator credentials strictly."""
    user = authenticate_user(db, login_data)

    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Administrative privileges required for admin login.",
        )

    payload = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "language_id": user.language_id,
    }

    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "role": user.role,
    }


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Admin Profile (/admin/me)",
    description="Retrieves profile details of the currently authenticated administrator.",
)
def get_admin_profile(
    current_admin: User = Depends(get_current_admin_user),
) -> User:
    """Retrieve administrator profile."""
    return current_admin


@router.get(
    "/users",
    response_model=List[AdminUserSummaryResponse],
    summary="List all users (Admin Only)",
    description="Returns a paginated list of all system users. Requires ADMIN role.",
)
def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> List[User]:
    """Retrieve all users in the system."""
    return get_all_users(db, skip=skip, limit=limit)


@router.put(
    "/users/{user_identifier}/role",
    response_model=UserRoleUpdateResponse,
    summary="Update user role (Admin Only)",
    description="Promote or demote a user's role ('farmer' or 'admin') by user ID, email, or username. Requires ADMIN role.",
)
def change_user_role(
    user_identifier: str,
    role_data: UserRoleUpdateRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Update role for a target user (by ID, email, or username)."""
    updated_user = update_user_role(db, user_identifier, role_data, current_admin.id)
    return {
        "message": f"Successfully updated role for user '{updated_user.email}' to '{updated_user.role}'.",
        "user": updated_user,
    }


@router.put(
    "/users/{user_identifier}/status",
    response_model=UserStatusUpdateResponse,
    summary="Update user status (Admin Only)",
    description="Update user account status ('active', 'suspended', 'inactive') by user ID, email, or username. Requires ADMIN role.",
)
def change_user_status(
    user_identifier: str,
    status_data: UserStatusUpdateRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Update operational status for a target user (by ID, email, or username)."""
    updated_user = update_user_status(db, user_identifier, status_data, current_admin.id)
    return {
        "message": f"Successfully updated account status for user '{updated_user.email}' to '{updated_user.status}'.",
        "user": updated_user,
    }


@router.delete(
    "/users/{user_identifier}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user account (Admin Only)",
    description="Permanently delete a user account and associated history by user ID, email, or username. Requires ADMIN role.",
)
def remove_user(
    user_identifier: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete target user account (by ID, email, or username)."""
    delete_user_account(db, user_identifier, current_admin.id)


@router.get(
    "/analytics",
    response_model=AdminSystemAnalyticsResponse,
    summary="System-wide analytics (Admin Only)",
    description="Returns aggregate administrative metrics across the entire platform.",
)
def system_analytics(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> AdminSystemAnalyticsResponse:
    """Retrieve global system analytics."""
    return AdminSystemAnalyticsResponse(**get_system_analytics(db))
