from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from app.models import Language, User
from app.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    UserLoginRequest,
    UserRegisterRequest,
    UserUpdateRequest,
)
from app.security import get_password_hash, verify_password

def register_user(db: Session, user_data: UserRegisterRequest) -> User:
    """
    Registers a new user in the database.
    Checks for email conflict first. Hashes password using bcrypt.
    """
    # 0. Validate password match
    if user_data.password != user_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password and Confirm Password do not match."
        )

    # 1. Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        # Return 409 Conflict as requested
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflict: A user with this email address already exists."
        )
    
    # 2. Validate that the provided language exists before creating the user.
    language = db.query(Language).filter(Language.id == user_data.language_id).first()
    if not language:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid language_id. Please provide a valid predefined language id."
        )

    # 3. Hash the password
    hashed_password = get_password_hash(user_data.password)
    
    # 4. Create user entity
    db_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        language_id=user_data.language_id
    )
    
    # 4. Save to database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, login_data: UserLoginRequest) -> User:
    """
    Authenticates a user with email and password.
    Returns the user model if valid, raises HTTP 401 otherwise.
    """
    # 1. Fetch user by email
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        # Return 401 Unauthorized as requested
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 2. Verify hashed password matches
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Track the current UTC login time and commit it before returning the user.
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def update_user_profile(
    db: Session,
    current_user: User,
    user_data: UserUpdateRequest,
) -> User:
    """Update the authenticated user's email and preferred language."""
    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email, User.id != current_user.id)
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflict: A user with this email address already exists."
        )

    language = db.query(Language).filter(Language.id == user_data.language_id).first()
    if not language:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid language_id. Please provide a valid predefined language id."
        )

    current_user.email = user_data.email
    current_user.language_id = user_data.language_id
    db.commit()
    db.refresh(current_user)
    return current_user


def _ensure_password_confirmation(new_password: str, confirm_password: str) -> None:
    """Raise a client error when a submitted password confirmation does not match."""
    if new_password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password and Confirm Password do not match.",
        )


def _commit_password_update(db: Session) -> None:
    """Commit a password update and leave the session usable if persistence fails."""
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update password.",
        ) from exc


def change_user_password(
    db: Session,
    current_user: User,
    password_data: ChangePasswordRequest,
) -> None:
    """Verify and replace the authenticated user's password."""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    _ensure_password_confirmation(
        password_data.new_password,
        password_data.confirm_password,
    )

    if verify_password(password_data.new_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password.",
        )

    user.hashed_password = get_password_hash(password_data.new_password)
    _commit_password_update(db)


def reset_user_password(
    db: Session,
    password_data: ForgotPasswordRequest,
) -> None:
    """Replace a user's password after locating the account by email."""
    user = db.query(User).filter(User.email == password_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    _ensure_password_confirmation(
        password_data.new_password,
        password_data.confirm_password,
    )

    user.hashed_password = get_password_hash(password_data.new_password)
    _commit_password_update(db)
