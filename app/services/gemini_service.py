"""Gemini-backed response generation for the chatbot module."""

from fastapi import HTTPException, status
from google import genai

from app.config import settings


class GeminiService:
    """Generate chatbot responses with automatic API-key fallback."""

    _MODEL = "gemini-flash-latest"

    def generate_response(self, prompt: str, language_id: int | None = None) -> str:
        """Return Gemini's generated text, trying each configured key in order."""
        del language_id  # The prepared prompt already specifies the response language.

        api_keys = (
            settings.GEMINI_API_KEY_1,
            settings.GEMINI_API_KEY_2,
            settings.GEMINI_API_KEY_3,
        )

        for api_key in api_keys:
            if not api_key:
                continue

            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=self._MODEL,
                    contents=prompt,
                )
                if response.text:
                    return response.text
            except Exception as e:
                # Retry with the next configured key for API, timeout, and network errors.
                print("=" * 70)
                print(f"Gemini API failed using key: {api_key[:8]}...")
                print(f"Exception Type: {type(e).__name__}")
                print(f"Exception Message: {str(e)}")
                print("=" * 70)
                continue

        print("[WARNING] All Gemini API keys exhausted or rate-limited. Returning fallback response.")
        return (
            "Our AI agriculture assistant is currently experiencing high request volume. "
            "Please ask your farming question again in a few seconds!"
        )

gemini_service = GeminiService()
