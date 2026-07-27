"""Test script to verify model loading with new TensorFlow and Keras versions."""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import json
from pathlib import Path
import tensorflow as tf
import keras

_MODEL_PATH = Path("app/ml_models/efficientnetb2_crop_prediction.keras")
model_config_path = _MODEL_PATH / "config.json"
model_weights_path = _MODEL_PATH / "model.weights.h5"

print(f"✓ Model path exists: {_MODEL_PATH.exists()}")
print(f"✓ Config path exists: {model_config_path.exists()}")
print(f"✓ Weights path exists: {model_weights_path.exists()}")

if model_config_path.exists() and model_weights_path.exists():
    with model_config_path.open("r", encoding="utf-8") as handle:
        model_config = json.load(handle)
    
    model = tf.keras.models.model_from_json(json.dumps(model_config))
    model.load_weights(model_weights_path)
    print("✓ Model loaded successfully")
    print(f"✓ Model name: {model.name}")
    print(f"✓ Model input shape: {model.input_shape}")
    print(f"✓ TensorFlow version: {tf.__version__}")
    print(f"✓ Keras version: {keras.__version__}")
else:
    print("✗ Required model files not found")
