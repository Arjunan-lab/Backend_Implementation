from __future__ import annotations

from datetime import datetime
from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Language(Base):
    """
    SQLAlchemy model representing the languages table.
    Stores predefined languages used by users.
    """
    __tablename__ = "languages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    language_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # Normalized relationship: users reference a language via language_id.
    users: Mapped[list[User]] = relationship(back_populates="language")


class User(Base):
    """
    SQLAlchemy model representing the users table.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    language_id: Mapped[int | None] = mapped_column(ForeignKey("languages.id"), nullable=True, index=True)

    # Login/logout tracking fields for future logout support.
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_logout_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Normalized relationship: each user belongs to exactly one language.
    language: Mapped[Language | None] = relationship(back_populates="users")

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    prediction_history: Mapped[list["PredictionHistory"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    chat_history: Mapped[list["ChatHistory"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class PredictionHistory(Base):
    """Stores a completed final recommendation for a user."""
    __tablename__ = "prediction_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    soil_image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    soil_type: Mapped[str] = mapped_column(String(100), nullable=False)
    soil_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    nitrogen: Mapped[float] = mapped_column(Float, nullable=False)
    phosphorus: Mapped[float] = mapped_column(Float, nullable=False)
    potassium: Mapped[float] = mapped_column(Float, nullable=False)
    ph: Mapped[float] = mapped_column(Float, nullable=False)
    organic_carbon: Mapped[float] = mapped_column(Float, nullable=False)
    electrical_conductivity: Mapped[float] = mapped_column(Float, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    humidity: Mapped[float] = mapped_column(Float, nullable=False)
    soil_health: Mapped[str] = mapped_column(String(100), nullable=False)
    soil_health_score: Mapped[float] = mapped_column(Float, nullable=False)
    soil_fertility_status: Mapped[str] = mapped_column(String(100), nullable=False)
    nutrient_deficiencies: Mapped[list] = mapped_column(JSON, nullable=False)
    recommended_crops: Mapped[list] = mapped_column(JSON, nullable=False)
    recommended_fertilizers: Mapped[list] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="prediction_history")


class ChatHistory(Base):
    """Stores chatbot conversations for an authenticated user."""
    __tablename__ = "chat_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    prediction_history_id: Mapped[int | None] = mapped_column(
        ForeignKey("prediction_history.id"),
        nullable=True,
        index=True,
    )
    user_message: Mapped[str] = mapped_column(String, nullable=False)
    question_language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    preferred_language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    assistant_response: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="chat_history")
