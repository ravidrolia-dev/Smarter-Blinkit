import cv2
import numpy as np
import base64
import asyncio
from functools import partial
from scipy.spatial.distance import cosine

def _encode_face_sync(image_base64: str):
    """Synchronous face encoding — run in thread pool to avoid blocking event loop."""
    try:
        from deepface import DeepFace

        # Handle both plain base64 and data URL formats
        if "," in image_base64:
            img_data = base64.b64decode(image_base64.split(",")[1])
        else:
            img_data = base64.b64decode(image_base64)

        np_arr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img is None:
            return None

        # Extract highly robust embedding (ArcFace handles large pose/lighting variations)
        # align=True corrects face angle
        # enforce_detection=True ensures there is actually a face
        objs = DeepFace.represent(
            img_path=img, 
            model_name="ArcFace", 
            detector_backend="opencv", 
            enforce_detection=True, 
            align=True
        )
        
        if not objs or len(objs) == 0:
            return None
            
        return objs[0]["embedding"]
    except ValueError as e:
        print("Face detection failed (No face found):", e)
        return None
    except Exception as e:
        print("Error during face encoding:", e)
        return None


async def encode_face_from_base64(image_base64: str):
    """Async wrapper — runs DeepFace in a thread pool so it doesn't freeze the server."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_encode_face_sync, image_base64))


def compare_face(known_encoding, new_encoding_list) -> float:
    """
    Compare two ArcFace embeddings using Cosine Distance.
    Returns the distance (0.0 is perfect match, 2.0 is opposite).
    Lower distance means a better match.
    """
    if known_encoding is None or new_encoding_list is None:
        return 10.0
    try:
        a = np.array(known_encoding, dtype=np.float32)
        b = np.array(new_encoding_list, dtype=np.float32)

        # Protect against old 10,000-dimensional OpenCV flattened arrays
        if len(a) != len(b):
            print(f"Dimension mismatch: {len(a)} vs {len(b)}")
            return 10.0
        
        distance = cosine(a, b)
        print(f"Face Match Distance (Cosine): {distance:.4f}")
        return float(distance)
    except Exception as e:
        print("Error comparing faces:", e)
        return 10.0