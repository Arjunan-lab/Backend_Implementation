"""Prompt builders for the chatbot service."""

from app.models import PredictionHistory


def _language_requirements(language: str | None) -> str:
    language = language or "English"
    native_script = {
        "English": "English",
        "Telugu": "\u0c24\u0c46\u0c32\u0c41\u0c17\u0c41",
        "Hindi": "\u0939\u093f\u0928\u094d\u0926\u0940",
        "Tamil": "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd",
    }.get(language, language)
    return (
        f"Detect the user's question language silently. Answer only in {language}, using native "
        f"{native_script} script. Do not mix languages or transliterate."
    )


def build_general_farming_prompt(question: str, language_name: str | None) -> str:
    return f"You are a helpful agriculture assistant.\nQuestion: {question}\n{_language_requirements(language_name)}"


def build_prediction_explanation_prompt(question: str, prediction: PredictionHistory, language_name: str | None) -> str:
    return (
        f"You are a helpful agriculture assistant.\nQuestion: {question}\n"
        f"Soil type: {prediction.soil_type}\nSoil health: {prediction.soil_health}\n"
        f"Soil health score: {prediction.soil_health_score}\n"
        f"Soil fertility status: {prediction.soil_fertility_status}\n"
        f"{_language_requirements(language_name)}"
    )


def build_disease_explanation_prompt(question: str, language_name: str | None) -> str:
    return (
        "You are a helpful crop disease assistant. Explain likely causes, safe next steps, "
        f"and when to consult a local agricultural expert.\nQuestion: {question}\n"
        f"{_language_requirements(language_name)}"
    )


def build_follow_up_prompt(question: str, previous_response: str, language_name: str | None) -> str:
    return (
        f"You are a helpful agriculture assistant.\nPrevious response: {previous_response}\n"
        f"Follow-up question: {question}\n{_language_requirements(language_name)}"
    )


def build_translation_prompt(response: str, source_language: str, target_language: str) -> str:
    return (
        "Translate this agriculture-assistant answer naturally and faithfully, preserving its meaning.\n"
        f"Source language: {source_language}\nTarget language: {target_language}\n"
        f"Answer: {response}\n{_language_requirements(target_language)}"
    )
