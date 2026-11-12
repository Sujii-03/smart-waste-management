"""Loads the trained model produced by ai_model/train.py. Never fabricates predictions."""
import json, os, threading

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "ai_model", "model")
MODEL_PATH = os.path.join(BASE, "waste_model.keras")
CLASSES_PATH = os.path.join(BASE, "classes.json")
IMG_SIZE = (224, 224)
_lock, _model, _classes = threading.Lock(), None, None

class ModelNotAvailable(Exception): pass

def _load():
    global _model, _classes
    with _lock:
        if _model is None:
            if not (os.path.exists(MODEL_PATH) and os.path.exists(CLASSES_PATH)):
                raise ModelNotAvailable("No trained model found. Run ai_model/train.py first.")
            try:
                import tensorflow as tf
            except ImportError as e:
                raise ModelNotAvailable("TensorFlow is not installed.") from e
            _model = tf.keras.models.load_model(MODEL_PATH)
            with open(CLASSES_PATH) as f: _classes = json.load(f)
    return _model, _classes

def predict(path):
    """Returns (category, confidence 0-1). Model includes its own MobileNetV2 preprocessing."""
    model, classes = _load()
    import cv2, numpy as np  # OpenCV preprocessing; bilinear resize matches training
    img = cv2.imread(path)
    if img is None: raise ValueError("Unreadable image")
    img = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), IMG_SIZE, interpolation=cv2.INTER_LINEAR)
    x = np.expand_dims(img.astype("float32"), 0)
    probs = model.predict(x, verbose=0)[0]
    i = int(np.argmax(probs))
    return classes[i], float(probs[i])
