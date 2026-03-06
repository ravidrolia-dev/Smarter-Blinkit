import cv2
import numpy as np
import base64
import time
from services.scanner_service import _decode_barcode_sync

def test_performance():
    # Create a 720p dummy image with some noise
    img = np.zeros((720, 1280), dtype=np.uint8)
    cv2.putText(img, "TEST", (500, 360), cv2.FONT_HERSHEY_SIMPLEX, 5, 255, 5)
    
    _, buffer = cv2.imencode('.jpg', img)
    img_b64 = base64.b64encode(buffer).decode('utf-8')
    
    print("Testing scanning performance on 720p image...")
    start = time.time()
    res = _decode_barcode_sync(img_b64)
    elapsed = time.time() - start
    print(f"Result: {res['barcode']}")
    print(f"Total time taken: {elapsed:.3f}s")
    print(f"Blur Score: {res.get('blur_score')}")
    print(f"Brightness: {res.get('brightness')}")

if __name__ == "__main__":
    test_performance()
