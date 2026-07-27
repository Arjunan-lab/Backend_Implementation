from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth_routes import router as auth_router
from app.routes.prediction_routes import router as prediction_router
from app.routes.crop_routes import router as crop_router
from app.routes.nutrient_routes import router as nutrient_router
from app.routes.soil_fertility_routes import router as soil_fertility_router
from app.routes.soil_health_routes import router as soil_health_router
from app.routes.soil_health_score_routes import router as soil_health_score_router
from app.routes.final_recommendation_routes import router as final_recommendation_router
from app.routes.history_routes import router as history_router
from app.routes.task_routes import router as task_router
from app.routes.chat_routes import router as chat_router
from app.routes.analytics import router as analytics_router
from app.database import engine, Base

# Dynamic table creation fallback (useful for dev/test before running migrations)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="User Authentication API",
    description="Production-ready FastAPI backend with PostgreSQL, security best-practices, Alembic support, image prediction, and crop recommendation.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# CORS configuration (useful for frontend consumption)
app.add_middleware( 
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production environments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication endpoints
app.include_router(auth_router)
app.include_router(prediction_router)
app.include_router(crop_router)
app.include_router(nutrient_router)
app.include_router(soil_fertility_router)
app.include_router(soil_health_router)
app.include_router(soil_health_score_router)
app.include_router(final_recommendation_router)
app.include_router(history_router)
app.include_router(task_router)
app.include_router(chat_router)
app.include_router(analytics_router)

@app.get("/", tags=["Root"])
def root():
    """
    Root endpoint serving basic status checks.
    """
    return {
        "status": "online",
        "api_name": "User Authentication API",
        "docs_url": "/docs"
    }
