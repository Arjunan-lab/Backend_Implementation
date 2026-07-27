from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings

# Create engine for PostgreSQL connection
print("DATABASE_URL:", settings.DATABASE_URL)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True  # Check connection health before executing queries
)

# Create sessionmaker for dependency injection
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    """
    SQLAlchemy Declarative Base class for SQLAlchemy 2.0.
    """
    pass
