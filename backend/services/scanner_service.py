import cv2
import numpy as np
import base64
import zxingcpp
import asyncio
from functools import partial

def get_brightness(image):
    """Calculate mean brightness of the image (0-255)."""
    if len(image.shape) == 3:
        # Convert to LAB to get accurate perceived brightness
        return cv2.cvtColor(image, cv2.COLOR_BGR2LAB)[:,:,0].mean()
    return image.mean()

def get_blur_score(image):
    """Calculate blur score using Laplacian variance."""
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(image, cv2.CV_64F).var()

def detect_roi(gray):
    """
    Detect potential barcode regions (ROI) using vertical gradients.
    Returns a list of cropped images.
    """
    # 1. Vertical Sobel filter to highlight barcode-like vertical bars
    grad_x = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
    grad_y = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=0, dy=1, ksize=-1)
    gradient = cv2.subtract(cv2.convertScaleAbs(grad_x), cv2.convertScaleAbs(grad_y))

    # 2. Blur and threshold
    blurred = cv2.blur(gradient, (9, 9))
    _, thresh = cv2.threshold(blurred, 225, 255, cv2.THRESH_BINARY)

    # 3. Morphological closing to join the bars into a single block
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 7))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # 4. Filter contours by aspect ratio and size
    contours, _ = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rois = []
    height, width = gray.shape

    for c in contours:
        rect = cv2.minAreaRect(c)
        box = cv2.boxPoints(rect)
        box = np.int0(box)

        # Get bounding box
        x, y, w, h = cv2.boundingRect(c)
        
        # Filtering criteria for barcodes
        if w < 50 or h < 20: continue
        aspect_ratio = w / float(h)
        if aspect_ratio < 0.5 or aspect_ratio > 10: continue

        # Add padding
        padding = 10
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(width, x + w + padding)
        y2 = min(height, y + h + padding)
        
        rois.append(gray[y1:y2, x1:x2])
    
    return rois

def preprocess_for_high_accuracy(gray):
    """
    Professional preprocessing: CLAHE + Blur + Morphological Cleanup.
    """
    # 1. CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # 2. Gaussian Blur to reduce noise
    blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)

    # 3. Morphological Closing (helps repair broken barcode lines)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(blurred, cv2.MORPH_CLOSE, kernel)

    return closed

def _decode_barcode_sync(image_base64: str):
    """
    Professional-grade scanning pipeline.
    Returns: (barcode_text, metadata_dict)
    """
    metadata = {
        "barcode": None,
        "low_light": False,
        "is_blurry": False,
        "brightness": 0,
        "blur_score": 0
    }

    try:
        if not image_base64:
            return metadata

        # Handle base64 / data URL
        if "," in image_base64:
            img_data = base64.b64decode(image_base64.split(",")[1])
        else:
            img_data = base64.b64decode(image_base64)

        np_arr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img is None:
            return metadata

        # 1. Diagnostics: Blur & Lighting
        brightness = float(get_brightness(img))
        blur_score = float(get_blur_score(img))
        
        metadata["brightness"] = brightness
        metadata["blur_score"] = blur_score
        metadata["low_light"] = brightness < 60
        metadata["is_blurry"] = blur_score < 70
        
        if metadata["is_blurry"]:
            return metadata

        # 2. Convert to Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 3. Direct Decoding (Zxing is very good even on raw)
        results = zxingcpp.read_barcodes(gray)
        if results:
            metadata["barcode"] = results[0].text
            return metadata

        # 4. Advanced Preprocessing Pipeline
        preprocessed = preprocess_for_high_accuracy(gray)
        results = zxingcpp.read_barcodes(preprocessed)
        if results:
            metadata["barcode"] = results[0].text
            return metadata

        # 5. ROI Based Decoding (Targeted)
        rois = detect_roi(gray)
        for roi in rois:
            # Try original and preprocessed ROI
            results = zxingcpp.read_barcodes(roi)
            if not results:
                roi_prep = preprocess_for_high_accuracy(roi)
                results = zxingcpp.read_barcodes(roi_prep)
            
            if results:
                metadata["barcode"] = results[0].text
                return metadata

        # 6. Final Resort: Upscale + Canny
        upscaled = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_LANCZOS4)
        edges = cv2.Canny(upscaled, 100, 200)
        results = zxingcpp.read_barcodes(edges)
        if results:
            metadata["barcode"] = results[0].text
            return metadata

        return metadata
    except Exception as e:
        print(f"Error in professional scanning pipeline: {e}")
        return metadata

async def decode_barcode(image_base64: str):
    """Async wrapper for professional barcode decoding."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_decode_barcode_sync, image_base64))
