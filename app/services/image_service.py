"""Reusable image prediction service for soil classification."""

import json
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import tensorflow as tf

from app.image_preprocessing import preprocess_image
from app.services.sarvam_service import translate_text


_MODEL_PATH = Path("app/ml_models/efficientnetb2_crop_prediction.keras")
_CLASS_NAMES_PATH = Path(__file__).resolve().parents[1] / "ml_models" / "class_names.json"

_MODEL: Optional[tf.keras.Model] = None
_CLASS_NAMES: Optional[List[str]] = None


def _remove_quantization_config(value: Any) -> None:
    """Remove legacy quantization settings from a model configuration in place."""
    if isinstance(value, dict):
        value.pop("quantization_config", None)
        for nested_value in value.values():
            _remove_quantization_config(nested_value)
    elif isinstance(value, list):
        for nested_value in value:
            _remove_quantization_config(nested_value)


def _load_model_once() -> tf.keras.Model:
    """Load the TensorFlow model once and reuse it for future predictions."""
    global _MODEL

    if _MODEL is None:
        if not _MODEL_PATH.exists():
            raise FileNotFoundError(f"Model file not found: {_MODEL_PATH}")

        try:
            model_config_path = _MODEL_PATH / "config.json"
            model_weights_path = _MODEL_PATH / "model.weights.h5"

            if not model_config_path.exists() or not model_weights_path.exists():
                raise FileNotFoundError(f"Model config or weights not found in {_MODEL_PATH}")

            with model_config_path.open("r", encoding="utf-8") as handle:
                model_config = json.load(handle)

            _remove_quantization_config(model_config)
            _MODEL = tf.keras.models.model_from_json(json.dumps(model_config))
            _MODEL.load_weights(model_weights_path)
            # Temporary debug logging for verification; can be removed later.
            print(f"[DEBUG] TensorFlow model loaded successfully from: {_MODEL_PATH}")
        except Exception as exc:  # pragma: no cover - defensive path
            traceback.print_exc()
            print(f"Original exception message: {exc}")
            raise RuntimeError(f"Failed to load model from {_MODEL_PATH}") from exc

    return _MODEL


def _load_class_names_once() -> List[str]:
    """Load class names once and reuse them for all predictions."""
    global _CLASS_NAMES

    if _CLASS_NAMES is None:
        if not _CLASS_NAMES_PATH.exists():
            raise FileNotFoundError(f"Class names file not found: {_CLASS_NAMES_PATH}")

        try:
            with _CLASS_NAMES_PATH.open("r", encoding="utf-8") as handle:
                loaded_names = json.load(handle)
        except (json.JSONDecodeError, OSError) as exc:
            raise RuntimeError(f"Failed to load class names from {_CLASS_NAMES_PATH}") from exc

        if not isinstance(loaded_names, list) or not all(isinstance(item, str) for item in loaded_names):
            raise ValueError("Class names file must contain a JSON array of strings.")

        _CLASS_NAMES = loaded_names
        # Temporary debug logging for verification; can be removed later.
        print(f"[DEBUG] Loaded class names from {_CLASS_NAMES_PATH}: {_CLASS_NAMES}")

    return _CLASS_NAMES


def predict_soil(image_path: str, language_id: int | None = None) -> Dict[str, Any]:
    """Predict the soil type for an image and return a reusable result payload.

    Args:
        image_path: File path to the input image.

    Returns:
        A dictionary containing the canonical English soil type, its translated
        display value, and the confidence score.

    Raises:
        ValueError: If the image path is invalid or the image cannot be processed.
        FileNotFoundError: If the model or class names file is missing.
        RuntimeError: If prediction fails.
    """
    if not image_path or not str(image_path).strip():
        raise ValueError("image_path must be a non-empty string.")

    print(f"[DEBUG] Received image path: {image_path}")
    image_file = Path(image_path)
    print(f"[DEBUG] Absolute path: {image_file.resolve()}")
    print(f"[DEBUG] Exists: {image_file.exists()}")

    try:
        processed_image = preprocess_image(image_path)
    except (FileNotFoundError, ValueError) as exc:
        raise ValueError(f"Invalid image: {image_path}") from exc

    model = _load_model_once()
    class_names = _load_class_names_once()

    # Temporary debug logging for verification; can be removed later.
    print(f"[DEBUG] Preprocessed image shape: {processed_image.shape}")

    try:
        predictions = model.predict(processed_image, verbose=0)
        # Temporary debug logging for verification; can be removed later.
        print(f"[DEBUG] Raw prediction probabilities: {predictions[0]}")
        predicted_index = int(np.argmax(predictions[0]))
        confidence_score = float(np.max(predictions[0]) * 100)
        # Temporary debug logging for verification; can be removed later.
        print(f"[DEBUG] Predicted class index: {predicted_index}")
        print(f"[DEBUG] Confidence score: {confidence_score}")
    except Exception as exc:
        raise RuntimeError("Prediction failed during model inference.") from exc

    if predicted_index < 0 or predicted_index >= len(class_names):
        raise RuntimeError("Predicted class index is out of range for the available class names.")

    canonical_soil_type = class_names[predicted_index]
    # Temporary debug logging for verification; can be removed later.
    print(f"[DEBUG] Final canonical soil type: {canonical_soil_type}")

    translated_soil_type = translate_text(canonical_soil_type, language_id)
    return {
        "canonical_soil_type": canonical_soil_type,
        "soil_type": translated_soil_type,
        "confidence": round(confidence_score, 2),
    }
