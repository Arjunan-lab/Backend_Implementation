"""Start the FastAPI server with the upgraded TensorFlow and Keras."""

import os
import sys

# Ensure the app module can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
import uvicorn

if __name__ == "__main__":
    print("✓ Starting FastAPI server with TensorFlow 2.21.0 and Keras 3.15.0")
    uvicorn.run(app, host="127.0.0.1", port=8000)
