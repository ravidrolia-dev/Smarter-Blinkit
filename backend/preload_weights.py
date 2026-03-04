from deepface import DeepFace
import numpy as np
import os

print("Starting ArcFace weights preload...")
dummy_img = np.zeros((224, 224, 3), dtype=np.uint8)
try:
    DeepFace.represent(img_path=dummy_img, model_name="ArcFace", enforce_detection=False, detector_backend="opencv")
    print("ArcFace loaded successfully!")
except Exception as e:
    print("Error:", e)
