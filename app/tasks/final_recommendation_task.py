"""Celery task for generating a complete soil recommendation."""

from typing import Any, Dict

from app.celery_app import celery_app
from app.database import SessionLocal
from app.services.crop_service import recommend_crop
from app.services.history_service import create_prediction_history
from app.services.image_service import predict_soil
from app.services.nutrient_service import predict_nutrient_deficiency
from app.services.soil_fertility_service import predict_soil_fertility
from app.services.soil_health_score_service import predict_soil_health_score
from app.services.soil_health_service import predict_soil_health


@celery_app.task(name="app.tasks.final_recommendation_task.generate_final_recommendation")
def generate_final_recommendation(
    image_path: str,
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    ph: float,
    organic_carbon: float,
    electrical_conductivity: float,
    temperature: float,
    humidity: float,
    language_id: int | None,
    user_id: int,
) -> Dict[str, Any]:
    """Run the final recommendation pipeline and persist its result."""
    db = SessionLocal()
    try:
        soil_prediction = predict_soil(image_path, language_id)
        canonical_soil_type = soil_prediction["canonical_soil_type"]
        translated_soil_type = soil_prediction["soil_type"]

        request_data = {
            "soil_type": canonical_soil_type,
            "nitrogen": nitrogen,
            "phosphorus": phosphorus,
            "potassium": potassium,
            "ph": ph,
            "organic_carbon": organic_carbon,
            "electrical_conductivity": electrical_conductivity,
            "temperature": temperature,
            "humidity": humidity,
        }

        crop_recommendation = recommend_crop(request_data, language_id)
        nutrient_analysis = predict_nutrient_deficiency(request_data, language_id)
        soil_fertility = predict_soil_fertility(request_data, language_id)
        soil_health = predict_soil_health(request_data, language_id)
        soil_health_score = predict_soil_health_score(request_data)

        create_prediction_history(
            db,
            {
                "user_id": user_id,
                "soil_image_path": image_path,
                "soil_type": canonical_soil_type,
                "soil_confidence": soil_prediction.get("confidence"),
                "nitrogen": nitrogen,
                "phosphorus": phosphorus,
                "potassium": potassium,
                "ph": ph,
                "organic_carbon": organic_carbon,
                "electrical_conductivity": electrical_conductivity,
                "temperature": temperature,
                "humidity": humidity,
                "soil_health": soil_health["soil_health"],
                "soil_health_score": soil_health_score["soil_health_score"],
                "soil_fertility_status": soil_fertility["soil_fertility_status"],
                "nutrient_deficiencies": nutrient_analysis["deficiencies"],
                "recommended_crops": crop_recommendation["recommended_crops"],
                "recommended_fertilizers": nutrient_analysis["recommended_fertilizers"],
            },
        )

        return {
            "soil_type": translated_soil_type,
            "soil_confidence": soil_prediction.get("confidence"),
            "soil_health": soil_health["soil_health"],
            "soil_health_score": soil_health_score["soil_health_score"],
            "soil_fertility_status": soil_fertility["soil_fertility_status"],
            "deficiencies": nutrient_analysis["deficiencies"],
            "recommended_crops": crop_recommendation["recommended_crops"],
            "recommended_fertilizers": nutrient_analysis["recommended_fertilizers"],
        }
    finally:
        db.close()
