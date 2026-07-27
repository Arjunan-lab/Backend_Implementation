"""Reusable soil fertility status prediction service."""

import pickle
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from app.services.sarvam_service import translate_text


_MODEL_PATH = Path("app/ml_models/soil_fertility_model.pkl")
_LABEL_ENCODERS_PATH = Path("app/ml_models/label_encoders.pkl")
_FEATURE_META_PATH = Path("app/ml_models/feature_meta.pkl")

_MODEL: Optional[Any] = None
_LABEL_ENCODERS: Optional[Dict[str, Any]] = None
_FEATURE_META: Optional[Dict[str, Any]] = None

SOIL_FERTILITY_MAPPING = {
    0: "Fertile",
    1: "Infertile",
    2: "Moderately Fertile",
}


def _load_model_once() -> Any:
    """Load the soil fertility model once and reuse it for future predictions."""
    global _MODEL

    if _MODEL is None:
        if not _MODEL_PATH.exists():
            raise FileNotFoundError(f"Model file not found: {_MODEL_PATH}")

        try:
            with _MODEL_PATH.open("rb") as handle:
                _MODEL = pickle.load(handle)
            print(f"[DEBUG] Soil fertility model loaded successfully from: {_MODEL_PATH}")
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
            return {}

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
            raise ValueError("Feature metadata file must contain a dictionary.")

        print(f"[DEBUG] Loaded feature metadata from {_FEATURE_META_PATH}: {_FEATURE_META}")

    return _FEATURE_META


def predict_soil_fertility(
    data: Dict[str, Any],
    language_id: int | None = None,
) -> Dict[str, Any]:
    """Predict soil fertility status from soil and environmental features."""
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
        fertility_encoder = label_encoders.get("Soil_Fertility_Status")
        if fertility_encoder is not None:
            soil_fertility_status = fertility_encoder.inverse_transform([int(predicted_value)])[0]
        else:
            soil_fertility_status = SOIL_FERTILITY_MAPPING.get(int(predicted_value))
            if soil_fertility_status is None:
                raise RuntimeError(f"Unknown soil fertility class: {predicted_value}")

        print(f"[DEBUG] Decoded soil fertility status: {soil_fertility_status}")

        return {
            "soil_fertility_status": translate_text(soil_fertility_status, language_id),
        }

    except Exception as exc:
        traceback.print_exc()
        raise RuntimeError(f"Soil fertility prediction failed: {str(exc)}") from exc
