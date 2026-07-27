"""Sarvam AI translation helper for final prediction labels."""

import json
from urllib.request import Request, urlopen

from app.config import settings


_LANGUAGE_CODES = {
    1: "en-IN",
    2: "te-IN",
    3: "hi-IN",
    4: "ta-IN",
}


def translate_text(text: str, language_id: int) -> str:
    """Translate an English response label, returning the original text on failure."""
    target_language_code = _LANGUAGE_CODES.get(language_id)
    if language_id == 1 or target_language_code is None:
        return text

    try:
        payload = json.dumps({
            "input": text,
            "source_language_code": "en-IN",
            "target_language_code": target_language_code,
        }).encode("utf-8")
        request = Request(
            settings.SARVAM_API_URL,
            data=payload,
            headers={
                "api-subscription-key": settings.SARVAM_API_KEY,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(request, timeout=10) as response:
            translated_text = json.loads(response.read().decode("utf-8")).get("translated_text")

        return translated_text if isinstance(translated_text, str) else text
    except Exception:
        return text
