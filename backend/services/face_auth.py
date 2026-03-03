import face_recognition
import numpy as np
import base64
import io
from PIL import Image
from typing import Optional, List

def encode_face_from_base64(image_b64: str) -> Optional[List[float]]:
    """Extract face encoding from a base64 image string."""
    try:
        # Decode base64
        if "," in image_b64:
            image_b64 = image_b64.split(",")[1]
        image_bytes = base64.b64decode(image_b64)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_array = np.array(image)

        # Get face encodings
        encodings = face_recognition.face_encodings(image_array)
        if not encodings:
            return None
        return encodings[0].tolist()
    except Exception as e:
        print(f"Face encoding error: {e}")
        return None

def compare_face(known_encoding: List[float], image_b64: str, tolerance: float = 0.5) -> bool:
    """Compare a known encoding with a face in a base64 image."""
    try:
        candidate_encoding = encode_face_from_base64(image_b64)
        if candidate_encoding is None:
            return False
        results = face_recognition.compare_faces(
            [np.array(known_encoding)],
            np.array(candidate_encoding),
            tolerance=tolerance
        )
        return bool(results[0])
    except Exception as e:
        print(f"Face comparison error: {e}")
        return False
