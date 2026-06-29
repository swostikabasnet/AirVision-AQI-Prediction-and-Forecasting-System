import os
import numpy as np
import tensorflow as tf
from PIL import Image

_image_model = None
MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "models",
    "aqi_classifier_model.keras"
)

CLASS_MAP = {
    0: {
        "status": "Good",
        "predicted_aqi": 35,
        "health_advice": "Air quality is satisfactory. Enjoy outdoor activities."
    },
    1: {
        "status": "Moderate",
        "predicted_aqi": 75,
        "health_advice": "Moderate air quality. Sensitive groups should limit prolonged outdoor exertion."
    },
    2: {
        "status": "Unhealthy",
        "predicted_aqi": 165,
        "health_advice": "Reduce outdoor activities. Wear a mask when going outside."
    },
}

# Map class 3 (if model predicts it) to Unhealthy
CLASS_MAP_EXPECTED = {0, 1, 2}

def get_image_model():
    global _image_model
    if _image_model is None:
        # Load the trained CNN model for image classification
        _image_model = tf.keras.models.load_model(MODEL_PATH)
    return _image_model

def predict_aqi_from_image(image_file):
    """
    Classify the sky image using the trained CNN model.
    Classes map to: 0 -> Good, 1 -> Moderate, 2 -> Unhealthy, 3 -> Unhealthy for Sensitive Groups
    """
    try:
        # Load and preprocess image
        if hasattr(image_file, 'seek'):
            image_file.seek(0)
        img = Image.open(image_file)
        img = img.convert('RGB')
        img = img.resize((150, 150))
        
        # Preprocess: rescale 1./255 and add batch dimension
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        
        # Run prediction
        model = get_image_model()
        preds = model.predict(img_array)
        pred_class_idx = int(np.argmax(preds[0]))
        
        # Map class 3 (if predicted) to Unhealthy — only 3 classes used
        if pred_class_idx not in CLASS_MAP_EXPECTED:
            pred_class_idx = 2
        
        # Map prediction index to metadata
        res = CLASS_MAP.get(pred_class_idx, CLASS_MAP[1]) # Default to Moderate if mismatch
        
        return res
    except Exception as e:
        # Fallback to moderate in case of any processing errors
        return {
            "predicted_aqi": 75,
            "status": "Moderate",
            "health_advice": f"Error running classifier: {str(e)}. Defaulting to moderate."
        }

