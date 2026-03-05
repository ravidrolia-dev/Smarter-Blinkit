import sys
import cv2
try:
    from pyzbar.pyzbar import decode
except ImportError as e:
    print(f"Failed to import pyzbar: {e}")
    sys.exit(1)

def test(img_path):
    img = cv2.imread(img_path)
    if img is None:
        print("Failed to load image")
        return
    results = decode(img)
    if results:
        print(f"Decoded: {results[0].data.decode('utf-8')}")
    else:
        print("Failed to decode")

if __name__ == "__main__":
    test(sys.argv[1])
