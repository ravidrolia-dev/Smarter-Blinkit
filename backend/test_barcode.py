import cv2
import zxingcpp
import sys
import numpy as np

def run_test(image_path):
    print(f"Testing image: {image_path}")
    img = cv2.imread(image_path)
    if img is None:
        print("Could not read image.")
        return

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    ZXING_FORMATS = (
        zxingcpp.BarcodeFormat.Code128,
        zxingcpp.BarcodeFormat.Code39,
        zxingcpp.BarcodeFormat.Code93,
        zxingcpp.BarcodeFormat.DataMatrix,
        zxingcpp.BarcodeFormat.QRCode,
        zxingcpp.BarcodeFormat.EAN13,
        zxingcpp.BarcodeFormat.UPCA,
        zxingcpp.BarcodeFormat.EAN8
    )

    print("\n--- Try 1: Raw Grayscale ---")
    results = zxingcpp.read_barcodes(gray, formats=ZXING_FORMATS)
    if results:
        print(f"Success! {results[0].text}")
    else:
        print("Failed.")

    print("\n--- Try 2: CLAHE + Morphological Closing (Production Pipeline) ---")
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    sharpen_kernel = np.array([[-1, 2, -1], [-1, 2, -1], [-1, 2, -1]])
    sharpened = cv2.filter2D(enhanced, -1, sharpen_kernel)
    enhanced = cv2.addWeighted(enhanced, 0.8, sharpened, 0.2, 0)
    blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    results = zxingcpp.read_barcodes(closed, formats=ZXING_FORMATS)
    if results:
        print(f"Success! {results[0].text}")
    else:
        print("Failed.")

    print("\n--- Try 3: Basic Threshold ---")
    _, thresh_basic = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    results = zxingcpp.read_barcodes(thresh_basic, formats=ZXING_FORMATS)
    if results:
         print(f"Success! {results[0].text}")
    else:
         print("Failed.")

    print("\n--- Try 4: Try Invert (Zxing option) ---")
    results = zxingcpp.read_barcodes(gray, formats=ZXING_FORMATS, try_invert=True, try_downscale=True)
    if results:
         print(f"Success! {results[0].text}")
    else:
         print("Failed.")

    # Isolate Barcode (Crop out white/black borders to help binarizer)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    coords = cv2.findNonZero(thresh)
    if coords is not None:
        x, y, w, h = cv2.boundingRect(coords)
        x_pad, y_pad = 10, 10
        x1 = max(0, x - x_pad)
        y1 = max(0, y - y_pad)
        x2 = min(gray.shape[1], x + w + x_pad)
        y2 = min(gray.shape[0], y + h + y_pad)
        cropped = gray[y1:y2, x1:x2]
        
        # Heavy crop for barcodes with text that throws off the reader
        h_crop = int(cropped.shape[0] * 0.20)
        heavy_crop = cropped[h_crop:-h_crop, :]
        print(f"\nCropped image size: {cropped.shape}, Heavy Crop: {heavy_crop.shape}")
    else:
        cropped = gray
        heavy_crop = gray

    print("\n--- Try 5: Pure Zxing on Heavy Crop ---")
    results = zxingcpp.read_barcodes(heavy_crop, formats=ZXING_FORMATS)
    if results: print(f"Success! {results[0].text}")
    else: print("Failed.")

    print("\n--- Try 6: Heavy Crop + Blur + Invert ---")
    results = zxingcpp.read_barcodes(heavy_crop, formats=ZXING_FORMATS, try_invert=True, try_downscale=True)
    if results: print(f"Success! {results[0].text}")
    else: print("Failed.")

    print("\n--- Try 7: Scaled Down (50%) Heavy Crop ---")
    scaled = cv2.resize(heavy_crop, (0,0), fx=0.5, fy=0.5)
    results = zxingcpp.read_barcodes(scaled, formats=ZXING_FORMATS)
    if results: print(f"Success! {results[0].text}")
    else: print("Failed.")

    print("\n--- Try 8: Binarizer BoolCast on Heavy Crop ---")
    results = zxingcpp.read_barcodes(heavy_crop, formats=ZXING_FORMATS, binarizer=zxingcpp.Binarizer.BoolCast)
    if results: print(f"Success! {results[0].text}")
    else: print("Failed.")

    print("\n--- Try 9: Extreme Morphological Healing (Thickening lines) ---")
    _, thresh_ext = cv2.threshold(heavy_crop, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    # Erase horizontal lines
    kernel_horiz = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1))
    temp = cv2.erode(thresh_ext, kernel_horiz, iterations=1)
    thresh_ext = cv2.subtract(thresh_ext, temp)
    
    # Thicken vertical lines
    kernel_vert = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5))
    healed = cv2.morphologyEx(thresh_ext, cv2.MORPH_CLOSE, kernel_vert)
    
    # Invert back to normal
    healed = cv2.bitwise_not(healed)

    results = zxingcpp.read_barcodes(healed, formats=ZXING_FORMATS)
    if results: print(f"Success! {results[0].text}")
    else: print("Failed.")

    print("\n--- Try 10: PyZbar Fallback ---")
    try:
        from pyzbar.pyzbar import decode
        decoded = decode(img)
        if decoded:
            print(f"Success (pyzbar)! {decoded[0].data.decode('utf-8')}")
        else:
            print("Failed (pyzbar).")
    except ImportError:
        print("pyzbar not strictly installed/available, skipping.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_test(sys.argv[1])
    else:
        print("Usage: python test_barcode.py <image_path>")
