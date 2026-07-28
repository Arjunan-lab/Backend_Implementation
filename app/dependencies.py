from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.config import settings
from app.models import User
from app.utils import decode_token

# Define OAuth2 bearer scheme for API security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def get_db() -> Generator[Session, None, None]:
    """
    Dependency to provide a thread-safe database session for each request.
    Closes the connection after completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency that decodes the bearer JWT token and retrieves the current user.
    Raises HTTP 401 if credentials fail or expire.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decode and validate claims using the access secret
    payload = decode_token(token, settings.JWT_SECRET_KEY)
    if payload is None:
        raise credentials_exception
        
    email: str = payload.get("email")
    user_id: int = payload.get("user_id")
    if email is None or user_id is None:
        raise credentials_exception
        
    # Retrieve user from the database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    # Token Revocation Check: Verify if token was issued prior to user's last logout
    iat: float | None = payload.get("iat")
    if iat and user.last_logout_at:
        logout_timestamp = user.last_logout_at.timestamp()
        if iat < logout_timestamp - 1:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked due to logout. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return user


def require_roles(allowed_roles: list[str]):
    """
    Higher-order security dependency enforcing Role-Based Access Control (RBAC).
    Checks user role and raises HTTP 403 Forbidden if unauthorized.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Administrative privileges required.",
            )
        return current_user

    return role_checker


def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency requiring the authenticated user to possess the ADMIN role.
    Raises HTTP 403 Forbidden for non-admin users.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Administrative privileges required.",
        )
    return current_user

