"""Reusable nutrient deficiency prediction service."""

import pickle
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from app.services.sarvam_service import translate_text


_MODEL_PATH = Path("app/ml_models/nutrient_deficiency_model.pkl")
_LABEL_ENCODERS_PATH = Path("app/ml_models/label_encoders.pkl")
_FEATURE_META_PATH = Path("app/ml_models/feature_meta.pkl")

_MODEL: Optional[Any] = None
_LABEL_ENCODERS: Optional[Dict[str, Any]] = None
_FEATURE_META: Optional[Dict[str, Any]] = None

NUTRIENT_CLASS_MAPPING = {
    0: "Nitrogen",
    1: "Nitrogen, Phosphorus",
    2: "Nitrogen, Phosphorus, Potassium",
    3: "Nitrogen, Potassium",
    4: "No_deficiencies",
    5: "Phosphorus",
    6: "Phosphorus, Potassium",
    7: "Potassium",
}

FERTILIZER_MAP = {
    "nitrogen": [
        "Urea (46% N)",
        "Ammonium Sulphate",
        "Well-rotted farmyard manure",
    ],
    "phosphorus": [
        "DAP (Di-Ammonium Phosphate)",
        "Single Super Phosphate (SSP)",
        "Rock phosphate",
    ],
    "potassium": [
        "Muriate of Potash (MOP)",
        "Sulphate of Potash (SOP)",
        "Wood ash",
    ],
}


def _load_model_once() -> Any:
    """Load the nutrient deficiency model once and reuse it for future predictions."""
    global _MODEL

    if _MODEL is None:
        if not _MODEL_PATH.exists():
            raise FileNotFoundError(f"Model file not found: {_MODEL_PATH}")

        try:
            with _MODEL_PATH.open("rb") as handle:
                _MODEL = pickle.load(handle)
            print(f"[DEBUG] Nutrient deficiency model loaded successfully from: {_MODEL_PATH}")
        except Exception as exc:  # pragma: no cover - defensive path
            traceback.print_exc()
            print(f"Original exception message: {exc}")
            raise RuntimeError(f"Failed to load model from {_MODEL_PATH}") from exc

    return _MODEL


def _load_label_encoders_once() -> Dict[str, Any]:
    """Load label encoders once and reuse them for all predictions."""
    global _LABEL_ENCODERS

    if _LABEL_ENCODERS is None:
        if not _LABEL_ENCODERS_PATH.exists():
            raise FileNotFoundError(f"Label encoders file not found: {_LABEL_ENCODERS_PATH}")

        try:
            with _LABEL_ENCODERS_PATH.open("rb") as handle:
                _LABEL_ENCODERS = pickle.load(handle)
        except (pickle.UnpicklingError, OSError) as exc:
            raise RuntimeError(f"Failed to load label encoders from {_LABEL_ENCODERS_PATH}") from exc

        if not isinstance(_LABEL_ENCODERS, dict):
            raise ValueError("Label encoders file must contain a dictionary.")

        print(f"[DEBUG] Loaded label encoders from {_LABEL_ENCODERS_PATH}: {list(_LABEL_ENCODERS.keys())}")

    return _LABEL_ENCODERS


def _load_feature_meta_once() -> Dict[str, Any]:
    """Load feature metadata once and reuse it for all predictions."""
    global _FEATURE_META

    if _FEATURE_META is None:
        if not _FEATURE_META_PATH.exists():
            raise FileNotFoundError(f"Feature metadata file not found: {_FEATURE_META_PATH}")

        try:
            with _FEATURE_META_PATH.open("rb") as handle:
                _FEATURE_META = pickle.load(handle)
        except (pickle.UnpicklingError, OSError) as exc:
            raise RuntimeError(f"Failed to load feature metadata from {_FEATURE_META_PATH}") from exc

        if not isinstance(_FEATURE_META, dict):
            raise ValueError("Feature metadata must contain a dictionary.")

        print(f"[DEBUG] Loaded feature metadata from {_FEATURE_META_PATH}: {_FEATURE_META}")

    return _FEATURE_META


def _get_recommended_fertilizers(deficiencies: list[str]) -> list[str]:
    """Return unique fertilizer recommendations in nutrient prediction order."""
    fertilizers: list[str] = []
    for deficiency in deficiencies:
        for fertilizer in FERTILIZER_MAP.get(deficiency.lower(), []):
            if fertilizer not in fertilizers:
                fertilizers.append(fertilizer)
    return fertilizers


def predict_nutrient_deficiency(
    data: Dict[str, Any],
    language_id: int | None = None,
) -> Dict[str, Any]:
    """Predict nutrient deficiencies from soil and environmental features."""
    try:
        model = _load_model_once()
        feature_meta = _load_feature_meta_once()

        print(f"[DEBUG] Received data: {data}")

        feature_order = feature_meta.get("input_features", feature_meta.get("feature_order"))
        if not isinstance(feature_order, list) or not feature_order:
            raise ValueError("Feature metadata must define a non-empty input_features list.")

        categorical_inputs = feature_meta.get("categorical_inputs", [])
        if not isinstance(categorical_inputs, list):
            raise ValueError("Feature metadata categorical_inputs must be a list.")
        print(f"[DEBUG] Feature order from metadata: {feature_order}")
        print(f"[DEBUG] Categorical inputs from metadata: {categorical_inputs}")

        normalized_data = {
            key.replace("_", "").lower(): value
            for key, value in data.items()
        }
        features: Dict[str, Any] = {}
        for feature in feature_order:
            normalized_feature = feature.replace("_", "").lower()
            if normalized_feature not in normalized_data or normalized_data[normalized_feature] is None:
                raise ValueError(f"Missing feature: {feature}")

            value = normalized_data[normalized_feature]
            if feature in categorical_inputs:
                features[feature] = value
            else:
                features[feature] = float(value)

        feature_frame = pd.DataFrame([features], columns=feature_order)
        print(f"[DEBUG] Feature vector shape: {feature_frame.shape}")
        print(f"[DEBUG] Feature vector: {feature_frame}")

        prediction = model.predict(feature_frame)
        predicted_value = np.asarray(prediction).reshape(-1)[0]
        print(f"[DEBUG] Raw prediction: {prediction}")
        print(f"[DEBUG] Predicted class: {predicted_value}")

        label_encoders = _load_label_encoders_once()
        nutrient_encoder = label_encoders.get("Nutrient_Deficiencies")
        if nutrient_encoder is not None:
            predicted_deficiencies = nutrient_encoder.inverse_transform([int(predicted_value)])[0]
        else:
            predicted_deficiencies = NUTRIENT_CLASS_MAPPING.get(int(predicted_value))
            if predicted_deficiencies is None:
                raise RuntimeError(f"Unknown nutrient deficiency class: {predicted_value}")

        print(f"[DEBUG] Decoded nutrient deficiencies: {predicted_deficiencies}")

        if predicted_deficiencies == "No_deficiencies":
            return {"deficiencies": [], "recommended_fertilizers": []}

        nutrient_labels = [nutrient.strip() for nutrient in str(predicted_deficiencies).split(",")]
        deficiencies = [
            {"nutrient": translate_text(nutrient.strip(), language_id)}
            for nutrient in nutrient_labels
        ]
        recommended_fertilizers = [
            {"fertilizer": translate_text(fertilizer, language_id)}
            for fertilizer in _get_recommended_fertilizers(nutrient_labels)
        ]
        return {
            "deficiencies": deficiencies,
            "recommended_fertilizers": recommended_fertilizers,
        }

    except Exception as exc:
        traceback.print_exc()
        raise RuntimeError(f"Nutrient deficiency prediction failed: {str(exc)}") from exc
