"""Image preprocessing utilities for soil image classification."""

from pathlib import Path

import numpy as np
import tensorflow as tf
from PIL import Image, UnidentifiedImageError
from tensorflow.keras.applications.efficientnet import preprocess_input


def preprocess_image(image_path: str) -> np.ndarray:
    """Load an image, resize it, normalize it, and return a model-ready array.

    The returned array has the shape (1, 224, 224, 3), which is suitable for
    TensorFlow image classification models that expect a batch of images.

    Args:
        image_path: File path to the input image.

    Returns:
        A NumPy array of shape (1, 224, 224, 3) with pixel values normalized
        to the range [0, 1].

    Raises:
        ValueError: If the image path is empty or the image cannot be processed.
        FileNotFoundError: If the image file does not exist.
    """
    if not image_path or not str(image_path).strip():
        raise ValueError("image_path must be a non-empty string.")

    image_file = Path(image_path)
    if not image_file.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    try:
        with Image.open(image_file) as image:
            rgb_image = image.convert("RGB")
            image_array = np.array(rgb_image, dtype=np.float32)
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError(f"Unable to read image from path: {image_path}") from exc

    if image_array.ndim != 3:
        raise ValueError("The loaded image must have three dimensions: height, width, channels.")

    resized_image = tf.image.resize(image_array, size=(224, 224), method="bilinear")
    resized_image = tf.cast(resized_image, tf.float32)
    preprocessed_image = preprocess_input(resized_image)
    processed_image = np.expand_dims(preprocessed_image.numpy(), axis=0)

    return processed_image
