"""Recreate the label encoders used by the crop recommendation models."""

import pickle
from pathlib import Path

import pandas as pd
from sklearn.preprocessing import LabelEncoder


PROJECT_ROOT = Path(__file__).resolve().parent
FEATURES_PATH = PROJECT_ROOT / "app" / "dataset" / "features.csv"
TARGETS_PATH = PROJECT_ROOT / "app" / "dataset" / "targets.csv"
OUTPUT_PATH = PROJECT_ROOT / "app" / "ml_models" / "label_encoders.pkl"


def main() -> None:
    features = pd.read_csv(FEATURES_PATH)
    targets = pd.read_csv(TARGETS_PATH)

    soil_encoder = LabelEncoder()
    soil_encoder.fit(features["Soil_Type"])

    crop_encoder = LabelEncoder()
    crop_encoder.fit(targets["Crop_Recommended"])

    encoders = {
        "soil_type": soil_encoder,
        "crop": crop_encoder,
    }

    with OUTPUT_PATH.open("wb") as handle:
        pickle.dump(encoders, handle)

    print("Soil_Type classes:", soil_encoder.classes_)
    print("Crop_Recommended classes:", crop_encoder.classes_)

    with OUTPUT_PATH.open("rb") as handle:
        verified_encoders = pickle.load(handle)

    print("Saved pickle keys:", verified_encoders.keys())


if __name__ == "__main__":
    main()
