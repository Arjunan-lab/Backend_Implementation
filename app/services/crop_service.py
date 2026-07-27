"""Reusable crop recommendation service for agricultural decision support."""

import pickle
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from app.services.sarvam_service import translate_text

_MODEL_PATH = Path("app/ml_models/crop_recommendation_model.pkl")
_LABEL_ENCODERS_PATH = Path("app/ml_models/label_encoders.pkl")
_FEATURE_META_PATH = Path("app/ml_models/feature_meta.pkl")

_MODEL: Optional[Any] = None
_LABEL_ENCODERS: Optional[Dict[str, Any]] = None
_FEATURE_META: Optional[Dict[str, Any]] = None


def _load_model_once() -> Any:
    """Load the crop recommendation model once and reuse it for future predictions."""
    global _MODEL

    if _MODEL is None:
        if not _MODEL_PATH.exists():
            raise FileNotFoundError(f"Model file not found: {_MODEL_PATH}")

        try:
            with _MODEL_PATH.open("rb") as handle:
                _MODEL = pickle.load(handle)
            # Temporary debug logging for verification; can be removed later.
            print(f"[DEBUG] Crop recommendation model loaded successfully from: {_MODEL_PATH}")
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

        # Temporary debug logging for verification; can be removed later.
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

        # Temporary debug logging for verification; can be removed later.
        print(f"[DEBUG] Loaded feature metadata from {_FEATURE_META_PATH}: {_FEATURE_META}")

    return _FEATURE_META


def recommend_crop(data: Dict[str, Any], language_id: int | None = None) -> Dict[str, Any]:
    """Recommend a crop based on soil and environmental conditions.

    Args:
        data: Dictionary containing soil and environmental features:
              - soil_type: Categorical soil type
              - nitrogen: Nitrogen content (N)
              - phosphorus: Phosphorus content (P)
              - potassium: Potassium content (K)
              - temperature: Temperature in Celsius
              - humidity: Humidity percentage
              - ph: Soil pH value
              - rainfall: Rainfall in mm

    Returns:
        A dictionary containing the five highest-confidence recommended crops.

    Raises:
        ValueError: If required fields are missing or invalid.
        FileNotFoundError: If model or metadata files are missing.
        RuntimeError: If prediction fails.
    """
    try:
        model = _load_model_once()
        feature_meta = _load_feature_meta_once()

        print(f"[DEBUG] Received data: {data}")

        # Arrange features according to feature_meta
        feature_order = feature_meta.get("input_features", feature_meta.get("feature_order"))
        if not isinstance(feature_order, list) or not feature_order:
            raise ValueError("Feature metadata must define a non-empty input_features list.")

        categorical_inputs = feature_meta.get("categorical_inputs", [])
        if not isinstance(categorical_inputs, list):
            raise ValueError("Feature metadata categorical_inputs must be a list.")
        print(f"[DEBUG] Feature order from metadata: {feature_order}")
        print(f"[DEBUG] Categorical inputs from metadata: {categorical_inputs}")

        # Build a DataFrame in metadata order, retaining categorical strings for CatBoost.
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

        # Rank every CatBoost class probability and return the five best crops.
        prediction = model.predict(feature_frame)
        probabilities = np.asarray(model.predict_proba(feature_frame))[0]
        top5_indices = np.argsort(probabilities)[::-1][:5]

        label_encoders = _load_label_encoders_once()
        crop_encoder = label_encoders.get("crop", None)
        if crop_encoder is None:
            raise RuntimeError("Crop label encoder not found in loaded encoders.")

        top5_crops = crop_encoder.inverse_transform(top5_indices.astype(int))

        print("=================================")
        print("PREDICTED CLASS")
        print("=================================")
        print(prediction)
        print()
        print("=================================")
        print("ALL PROBABILITIES")
        print("=================================")
        print(probabilities)
        print()
        print("=================================")
        print("MAX PROBABILITY")
        print("=================================")
        print(float(np.max(probabilities)))
        print()
        print("=================================")
        print("SUM OF PROBABILITIES")
        print("=================================")
        print(float(np.sum(probabilities)))
        print()
        print("=================================")
        print("TOP 5 INDICES")
        print("=================================")
        print(top5_indices)
        print()
        print("=================================")
        print("TOP 5 CROPS")
        print("=================================")
        for crop_name, index in zip(top5_crops, top5_indices):
            print(f"{crop_name} : {probabilities[index] * 100:.2f}%")

        recommendations = []
        for index in top5_indices:
            crop_name = crop_encoder.inverse_transform([int(index)])[0]
            recommendations.append({
                "crop": translate_text(crop_name, language_id),
            })

        return {"recommended_crops": recommendations}

    except Exception as exc:
        traceback.print_exc()
        raise RuntimeError(f"Crop recommendation failed: {str(exc)}") from exc
