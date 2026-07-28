import re
from datetime import datetime
from typing import Any
from pydantic import AliasChoices, BaseModel, EmailStr, Field, field_validator


from app.models import UserRole, UserStatus


class UserRegisterRequest(BaseModel):
    """
    Schema for register request body validation.
    """
    username: str | None = Field(default=None, description="Display username for the account.")
    email: EmailStr
    password: str = Field(..., description="User password. Must meet complexity requirements.")
    confirm_password: str = Field(..., description="Confirm password. Must be identical to password.")
    language_id: int = Field(..., description="ID of the predefined language from the languages table.")
    role: UserRole = Field(default=UserRole.FARMER, description="Role of the user ('farmer' or 'admin'). Defaults to 'farmer'.")
    region: str | None = Field(default=None, description="Geographical location or farming region.")
    admin_secret: str | None = Field(default=None, description="Secret key required when registering an Admin account ('AdminSecret123!').")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password_complexity(v)


def _validate_password_complexity(password: str) -> str:
    """Apply the password complexity rules used throughout the authentication API."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter (A-Z).")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter (a-z).")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit (0-9).")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("Password must contain at least one special character (e.g., !@#$%^&*).")
    return password

class UserRegisterResponse(BaseModel):
    """
    Schema for register response.
    """
    message: str


class ChangePasswordRequest(BaseModel):
    """Payload for an authenticated password change."""

    current_password: str
    new_password: str = Field(..., description="New password meeting the registration password rules.")
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return _validate_password_complexity(value)


class ForgotPasswordRequest(BaseModel):
    """Payload for resetting a password by email."""

    email: EmailStr
    new_password: str = Field(..., description="New password meeting the registration password rules.")
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return _validate_password_complexity(value)


class PasswordManagementResponse(BaseModel):
    """Confirmation returned after a password change or reset."""

    message: str


class LogoutResponse(BaseModel):
    """Response returned upon successful user logout, including username and role."""

    message: str = "Logged out successfully"
    username: str | None = None
    role: str = "farmer"


class UserUpdateRequest(BaseModel):
    """Schema for updating the authenticated user's profile."""
    username: str | None = None
    email: EmailStr
    language_id: int
    region: str | None = None


class UserRoleUpdateRequest(BaseModel):
    """Schema for updating a user's role (Admin only)."""
    username: str | None = Field(default=None, description="Username of the target account.")
    role: UserRole = Field(..., description="New role to assign to the user ('farmer' or 'admin').")


class UserStatusUpdateRequest(BaseModel):
    """Schema for updating a user's status (Admin only)."""
    status: UserStatus = Field(..., description="New operational status to assign to the user ('active', 'suspended', 'inactive').")


class UserLoginRequest(BaseModel):
    """
    Schema for login request.
    """
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """
    Schema for successful login token payload.
    """
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    role: str = "farmer"

class UserResponse(BaseModel):
    """
    Schema representing user profile details returned by API.
    """
    id: int
    username: str | None = None
    email: EmailStr
    role: str = "farmer"
    status: str = "active"
    region: str | None = None
    language_id: int | None
    created_at: datetime
    last_login_at: datetime | None
    last_logout_at: datetime | None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "john_farmer",
                "email": "user@example.com",
                "role": "farmer",
                "status": "active",
                "region": "Telangana",
                "language_id": 1,
                "created_at": "2026-07-21T10:30:00Z",
                "last_login_at": "2026-07-21T10:30:00Z",
                "last_logout_at": "2026-07-21T12:00:00Z"
            }
        }


class UserRoleUpdateResponse(BaseModel):
    """Response returned upon updating a user's security role."""

    message: str
    user: UserResponse


class UserStatusUpdateResponse(BaseModel):
    """Response returned upon updating a user's operational status."""

    message: str
    user: UserResponse


class AdminUserSummaryResponse(BaseModel):
    """Admin view of a system user."""
    id: int
    username: str | None = None
    email: EmailStr
    role: str
    status: str = "active"
    region: str | None = None
    language_id: int | None
    created_at: datetime
    last_login_at: datetime | None

    class Config:
        from_attributes = True


class AdminSystemAnalyticsResponse(BaseModel):
    """Global administrative statistics across the entire system."""
    total_users: int
    total_farmers: int
    total_admins: int
    active_users: int
    suspended_users: int
    recent_farmers_count: int
    total_predictions: int
    total_chat_messages: int
    users_by_region: dict[str, int]



class PredictionHistorySummaryResponse(BaseModel):
    """Lightweight prediction history response."""

    history_id: int
    id: int
    prediction_date: datetime
    soil_type: str
    soil_health: str
    soil_health_score: float
    soil_fertility_status: str
    top_crop: str | None


class PredictionHistoryDetailResponse(BaseModel):
    """Complete saved prediction history response."""

    history_id: int
    prediction_date: datetime
    soil_type: str
    soil_confidence: float | None
    nitrogen: float
    phosphorus: float
    potassium: float
    ph: float
    organic_carbon: float
    electrical_conductivity: float
    temperature: float
    humidity: float
    soil_health: str
    soil_health_score: float
    soil_fertility_status: str
    deficiencies: list[Any]
    recommended_crops: list[Any]
    recommended_fertilizers: list[Any]


class AnalyticsResponse(BaseModel):
    """Analytics totals and prediction summary for the authenticated user."""

    total_predictions: int
    total_crop_recommendations: int
    total_image_uploads: int
    prediction_history: int
    last_prediction: datetime | None = Field(
        None,
        description="Timestamp of the user's most recent prediction, if any.",
    )
    most_predicted_soil: str | None = Field(
        None,
        description=(
            "The most frequent soil type in the user's prediction history, "
            "translated to the user's preferred language when available."
        ),
    )


class ChatRequest(BaseModel):
    """Schema for an authenticated chatbot request."""
    question: str = Field(
        ...,
        validation_alias=AliasChoices("question", "message"),
        min_length=1,
        description="The agriculture question asked by the user."
    )
    prediction_history_id: int | None = None


class ChatResponse(BaseModel):
    """Single-language or bilingual chatbot response."""
    response: str | None = None
    question_language: str | None = None
    preferred_language: str | None = None
    english_response: str | None = None
    telugu_response: str | None = None
    hindi_response: str | None = None
    tamil_response: str | None = None


class ChatHistoryResponse(BaseModel):
    """Schema for one saved chatbot conversation."""
    id: int
    user_message: str
    question_language: str | None
    preferred_language: str | None
    assistant_response: str
    created_at: datetime

    class Config:
        from_attributes = True


class TaskStatusResponse(BaseModel):
    """Task metadata returned by ``GET /tasks/{task_id}``."""

    task_id: str
    status: str = Field(description="Current Celery task state.")
    original_filename: str | None = Field(
        default=None,
        description="Name of the file supplied when the task was created.",
    )
    upload_time: datetime | None = Field(
        default=None,
        description="UTC timestamp when the task upload was accepted.",
    )


class WeatherResponse(BaseModel):
    """Current weather returned with a final recommendation."""

    location: str
    temperature: float
    humidity: int
    rainfall: float


class FinalRecommendationResponse(BaseModel):
    """Completed final recommendation returned by ``POST /final-recommendation``."""

    task_id: str
    soil_type: str
    soil_health: str
    soil_health_score: float
    soil_fertility_status: str
    deficiencies: list[Any]
    recommended_crops: list[Any]
    recommended_fertilizers: list[Any]
    weather: WeatherResponse
