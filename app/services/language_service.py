"""Language helpers for supported chatbot conversations."""

from collections import Counter


LANGUAGE_BY_ID = {
    1: "English",
    2: "Telugu",
    3: "Hindi",
    4: "Tamil",
}

LANGUAGE_RESPONSE_KEYS = {
    "English": "english_response",
    "Telugu": "telugu_response",
    "Hindi": "hindi_response",
    "Tamil": "tamil_response",
}

_SCRIPT_RANGES = {
    "Telugu": (0x0C00, 0x0C7F),
    "Hindi": (0x0900, 0x097F),
    "Tamil": (0x0B80, 0x0BFF),
}


def get_preferred_language(language_id: int | None) -> str:
    """Map the authenticated user's stored language ID to a supported language."""
    return LANGUAGE_BY_ID.get(language_id, "English")


def detect_question_language(question: str) -> str:
    """Detect supported native scripts, treating Latin-script input as English."""
    script_counts = Counter()
    for character in question:
        codepoint = ord(character)
        for language, (start, end) in _SCRIPT_RANGES.items():
            if start <= codepoint <= end:
                script_counts[language] += 1
                break

    if script_counts:
        return script_counts.most_common(1)[0][0]
    return "English"
