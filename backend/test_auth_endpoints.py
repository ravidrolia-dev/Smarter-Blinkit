import requests
import base64
import numpy as np
import cv2

# Create a dummy image
img = np.zeros((200, 200, 3), dtype=np.uint8)
_, buffer = cv2.imencode('.jpg', img)
b64_str = base64.b64encode(buffer).decode('utf-8')
data_uri = f"data:image/jpeg;base64,{b64_str}"

payload = {
    "email": "test422@example.com",
    "name": "Test",
    "password": "password123",
    "role": "buyer",
    "face_image_b64": data_uri
}

print("Testing Registration Endpoint...")
resp = requests.post("http://localhost:8000/auth/register", json=payload)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text}")

payload_login = {
    "image_b64": data_uri
}
print("\nTesting Face Login Endpoint...")
resp2 = requests.post("http://localhost:8000/auth/face-login", json=payload_login)
print(f"Status: {resp2.status_code}")
print(f"Response: {resp2.text}")
