"""CLI check: python -m ai_model.predict path/to/image.jpg  (same code path the web app uses)."""
import sys
from backend.services.classifier import predict, ModelNotAvailable

if __name__ == "__main__":
    if len(sys.argv) != 2: raise SystemExit("usage: python -m ai_model.predict <image>")
    try:
        cat, conf = predict(sys.argv[1]); print(f"{cat}  ({conf*100:.1f}%)")
    except ModelNotAvailable as e:
        raise SystemExit(str(e))
