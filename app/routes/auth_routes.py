from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.schemas import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    UserUpdateRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    PasswordManagementResponse,
    LogoutResponse,
)
from app.dependencies import get_db, get_current_user
from app.models import User
from app.auth import (
    authenticate_user,
    change_user_password,
    register_user,
    reset_user_password,
    update_user_profile,
)
from app.utils import create_access_token, create_refresh_token

# Create the router for authentication
router = APIRouter(tags=["Authentication"])

@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Registers a user and stores a securely-hashed password. Supports English, Hindi, Telugu, Tamil."
)
def register(
    user_data: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    register_user(db, user_data)
    return {"message": "User registered successfully"}

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Farmer Login Endpoint",
    description="Authenticates farmer credentials specifically. Administrative accounts are denied access with HTTP 403 Forbidden.",
)
def login(
    login_data: UserLoginRequest,
    db: Session = Depends(get_db)
):
    # Business logic layer authentication
    user = authenticate_user(db, login_data)

    if user.role != "farmer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Farmer credentials required for farmer login. Please use /admin/login for administrative access.",
        )
    
    # Standard payload structure: user_id, email, role, language_id
    payload = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "language_id": user.language_id
    }
    
    # Generate tokens using respective secret keys
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "role": user.role
    }
@router.post(
    "/token",
    response_model=TokenResponse,
    summary="OAuth2 Token Endpoint"
)
def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    login_data = UserLoginRequest(
        email=form_data.username,
        password=form_data.password
    )

    user = authenticate_user(db, login_data)

    payload = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "language_id": user.language_id
    }

    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "role": user.role
    }

@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user details",
    description="Protected endpoint. Decodes access token and retrieves current user profile data."
)
def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user details",
    description="Updates the authenticated user's email and preferred language."
)
def update_me(
    user_data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_user_profile(db, current_user, user_data)


@router.put(
    "/change-password",
    response_model=PasswordManagementResponse,
    status_code=status.HTTP_200_OK,
    summary="Change the current user's password",
    description="Requires a Bearer access token and the user's current password.",
)
def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the authenticated user's password."""
    change_user_password(db, current_user, password_data)
    return {"message": "Password updated successfully."}


@router.post(
    "/forgot-password",
    response_model=PasswordManagementResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset a password by email",
    description="Resets an existing user's password without OTP, email verification, or reset tokens.",
)
def forgot_password(
    password_data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """Reset a user's password after confirming the account email exists."""
    reset_user_password(db, password_data)
    return {"message": "Password reset successfully."}


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Log out the current user",
    description="Records the current UTC logout time for the authenticated user."
)
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LogoutResponse:
    """Record a successful logout for the authenticated user."""
    current_user.last_logout_at = datetime.now(timezone.utc)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return LogoutResponse(
        message="Logged out successfully",
        username=getattr(current_user, "username", None) or current_user.email.split("@")[0],
        role=current_user.role,
    )
