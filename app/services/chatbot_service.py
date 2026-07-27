"""Business logic for authenticated multilingual chatbot conversations."""

import json
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import ChatHistory, PredictionHistory, User
from app.schemas import ChatRequest
from app.services.agriculture_validator import is_agriculture_question
from app.services.gemini_service import gemini_service
from app.services.language_service import (
    LANGUAGE_RESPONSE_KEYS,
    detect_question_language,
    get_preferred_language,
)
from app.services.prompt_builder import (
    build_disease_explanation_prompt,
    build_follow_up_prompt,
    build_general_farming_prompt,
    build_prediction_explanation_prompt,
    build_translation_prompt,
)


NON_AGRICULTURE_RESPONSES = {
    "English": "I'm an agriculture assistant and can only answer agriculture and farming related questions.",
    "Telugu": "\u0c28\u0c47\u0c28\u0c41 \u0c35\u0c4d\u0c2f\u0c35\u0c38\u0c3e\u0c2f \u0c38\u0c02\u0c2c\u0c02\u0c27\u0c3f\u0c02\u0c1a\u0c3f\u0c28 \u0c2a\u0c4d\u0c30\u0c36\u0c4d\u0c28\u0c32\u0c15\u0c41 \u0c2e\u0c3e\u0c24\u0c4d\u0c30\u0c2e\u0c47 \u0c38\u0c2e\u0c3e\u0c27\u0c3e\u0c28\u0c02 \u0c07\u0c35\u0c4d\u0c35\u0c17\u0c32\u0c28\u0c41.",
    "Hindi": "\u092e\u0948\u0902 \u0915\u0947\u0935\u0932 \u0915\u0943\u0937\u093f \u0914\u0930 \u0916\u0947\u0924\u0940 \u0938\u0947 \u0938\u0902\u092c\u0902\u0927\u093f\u0924 \u092a\u094d\u0930\u0936\u094d\u0928\u094b\u0902 \u0915\u093e \u0909\u0924\u094d\u0924\u0930 \u0926\u0947 \u0938\u0915\u0924\u093e \u0939\u0942\u0901\u0964",
    "Tamil": "\u0ba8\u0bbe\u0ba9\u0bcd \u0bb5\u0bbf\u0bb5\u0b9a\u0bbe\u0baf\u0bae\u0bcd \u0bae\u0bb1\u0bcd\u0bb1\u0bc1\u0bae\u0bcd \u0b89\u0bb4\u0bb5\u0bc1 \u0ba4\u0bca\u0b9f\u0bb0\u0bcd\u0baa\u0bbe\u0ba9 \u0b95\u0bc7\u0bb3\u0bcd\u0bb5\u0bbf\u0b95\u0bb3\u0bc1\u0b95\u0bcd\u0b95\u0bc1 \u0bae\u0b9f\u0bcd\u0b9f\u0bc1\u0bae\u0bc7 \u0baa\u0ba4\u0bbf\u0bb2\u0bb3\u0bbf\u0b95\u0bcd\u0b95 \u0bae\u0bc1\u0b9f\u0bbf\u0baf\u0bc1\u0bae\u0bcd.",
}


@dataclass
class ChatResult:
    """Persisted chat conversation together with its API response payload."""

    history: ChatHistory
    response_payload: dict[str, str]


def _get_prediction_context(
    db: Session,
    user_id: int,
    prediction_history_id: int | None,
) -> PredictionHistory | None:
    if prediction_history_id is None:
        return None
    return (
        db.query(PredictionHistory)
        .filter(
            PredictionHistory.id == prediction_history_id,
            PredictionHistory.user_id == user_id,
        )
        .first()
    )


def _build_prompt(
    question: str,
    response_language: str,
    prediction: PredictionHistory | None,
    previous_chat: ChatHistory | None,
) -> str:
    if prediction is not None:
        return build_prediction_explanation_prompt(question, prediction, response_language)
    if "disease" in question.lower():
        return build_disease_explanation_prompt(question, response_language)
    if previous_chat is not None:
        return build_follow_up_prompt(question, previous_chat.assistant_response, response_language)
    return build_general_farming_prompt(question, response_language)


def _build_response_payload(
    question_language: str,
    preferred_language: str,
    primary_response: str,
    preferred_response: str | None = None,
) -> dict[str, str]:
    if question_language == preferred_language:
        return {"response": primary_response}
    return {
        "question_language": question_language,
        "preferred_language": preferred_language,
        LANGUAGE_RESPONSE_KEYS[question_language]: primary_response,
        LANGUAGE_RESPONSE_KEYS[preferred_language]: preferred_response or "",
    }


def chat_with_user(db: Session, current_user: User, chat_data: ChatRequest) -> ChatResult:
    """Validate, generate, and save a single-language or bilingual conversation."""
    prediction = _get_prediction_context(db, current_user.id, chat_data.prediction_history_id)
    if chat_data.prediction_history_id is not None and prediction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction history not found.")

    question_language = detect_question_language(chat_data.question)
    preferred_language = get_preferred_language(current_user.language_id)
    is_agriculture = is_agriculture_question(chat_data.question)

    if is_agriculture:
        previous_chat = (
            db.query(ChatHistory)
            .filter(ChatHistory.user_id == current_user.id)
            .order_by(ChatHistory.created_at.desc())
            .first()
        )
        primary_response = gemini_service.generate_response(
            _build_prompt(chat_data.question, question_language, prediction, previous_chat)
        )
        preferred_response = None
        if question_language != preferred_language:
            preferred_response = gemini_service.generate_response(
                build_translation_prompt(primary_response, question_language, preferred_language)
            )
    else:
        primary_response = NON_AGRICULTURE_RESPONSES[question_language]
        preferred_response = (
            NON_AGRICULTURE_RESPONSES[preferred_language]
            if question_language != preferred_language
            else None
        )

    response_payload = _build_response_payload(
        question_language,
        preferred_language,
        primary_response,
        preferred_response,
    )
    stored_response = (
        primary_response
        if question_language == preferred_language
        else json.dumps(response_payload, ensure_ascii=False)
    )

    chat_history = ChatHistory(
        user_id=current_user.id,
        prediction_history_id=prediction.id if prediction else None,
        user_message=chat_data.question,
        question_language=question_language,
        preferred_language=preferred_language,
        assistant_response=stored_response,
    )
    db.add(chat_history)
    db.commit()
    db.refresh(chat_history)
    return ChatResult(history=chat_history, response_payload=response_payload)


def get_user_chat_history(db: Session, user_id: int) -> list[ChatHistory]:
    """Return only the requesting user's conversations, newest first."""
    return (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == user_id)
        .order_by(ChatHistory.created_at.desc())
        .all()
    )
