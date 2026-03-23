try:
    import cv2
    import numpy as np
    HAS_CV2 = True
    # Initialize the legacy Haar Cascade classifier
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
except ImportError:
    cv2 = None
    np = None
    face_cascade = None
    HAS_CV2 = False

import base64
import asyncio
from functools import partial

def _encode_face_sync(image_base64: str):
    """Legacy Synchronous face encoding using basic OpenCV cropping. No strict checks."""
    if not HAS_CV2:
        return None
    try:
        # Handle both plain base64 and data URL formats
        if "," in image_base64:
            img_data = base64.b64decode(image_base64.split(",")[1])
        else:
            img_data = base64.b64decode(image_base64)

        np_arr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img is None:
            return None

        # Basic grayscale conversion and histogram equalization
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        
        # Detect faces with legacy Haar Cascade
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            return None

        # Take the first detected face, crop and resize
        (x, y, w, h) = faces[0]
        face = gray[y:y+h, x:x+w]
        face = cv2.resize(face, (100, 100))
        
        # Store as flattened grayscale array (10,000 dimensions)
        return face.flatten().tolist()
    except Exception as e:
        print(f"Legacy encoding error: {e}")
        return None

async def encode_face_from_base64(image_base64: str):
    """Async wrapper for the legacy encoding logic."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_encode_face_sync, image_base64))

def compare_face(known_encoding, new_encoding_list) -> float:
    """Legacy comparison using Template Matching (Correlation). Higher is better."""
    if not HAS_CV2 or known_encoding is None or new_encoding_list is None:
        return -1.0
    try:
        # Reconstruct the 100x100 grayscale images from the flattened lists
        known = np.array(known_encoding, dtype=np.uint8).reshape((100, 100))
        new = np.array(new_encoding_list, dtype=np.uint8).reshape((100, 100))
        
        # Use TM_CCOEFF_NORMED for brightness/contrast robustness
        res = cv2.matchTemplate(known, new, cv2.TM_CCOEFF_NORMED)
        match_score = float(res[0][0])
        print(f"Legacy Face Match Score: {match_score:.4f}")
        return match_score
    except Exception as e:
        print("Legacy comparison error:", e)
        return -1.0