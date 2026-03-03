import cv2
import numpy as np
import base64
import asyncio
from functools import partial

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

def _encode_face_sync(image_base64: str):
    """Synchronous face encoding — run in thread pool to avoid blocking event loop."""
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

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Normalize lighting to improve matching consistency
        gray = cv2.equalizeHist(gray)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            return None

        (x, y, w, h) = faces[0]
        face = gray[y:y+h, x:x+w]
        face = cv2.resize(face, (100, 100))
        return face.flatten().tolist()
    except Exception:
        return None


async def encode_face_from_base64(image_base64: str):
    """Async wrapper — runs OpenCV in a thread pool so it doesn't freeze the server."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_encode_face_sync, image_base64))


def compare_face(known_encoding, new_encoding_list) -> float:
    """Compare two face encodings using normalized cross-correlation. Returns 1.0 for perfect match, -1.0 for opposite. Higher is better."""
    if known_encoding is None or new_encoding_list is None:
        return -1.0
    try:
        # Reconstruct the 100x100 grayscale images from the flattened lists
        known = np.array(known_encoding, dtype=np.uint8).reshape((100, 100))
        new = np.array(new_encoding_list, dtype=np.uint8).reshape((100, 100))
        
        # TM_CCOEFF_NORMED handles brightness and contrast differences implicitly
        res = cv2.matchTemplate(known, new, cv2.TM_CCOEFF_NORMED)
        match_score = float(res[0][0])
        print(f"Face Match Score (Correlation): {match_score:.4f}")
        return match_score
    except Exception as e:
        print("Error comparing faces:", e)
        return -1.0