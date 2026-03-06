import cv2
import numpy as np
import base64
import zxingcpp
import asyncio
import time
from functools import partial

# Let ZXing use its default configuration which scans all formats including ITF, Code128, etc.

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
        box = np.intp(box)

        # Get bounding box
        x, y, w, h = cv2.boundingRect(c)
        
        # Filtering criteria for barcodes
        # Relaxed width to 30 to catch very small UPC-E barcodes
        if w < 30 or h < 20: continue
        aspect_ratio = w / float(h)
        # Allow much wider aspect ratios for alphanumeric barcodes (e.g. Code128)
        if aspect_ratio < 0.5 or aspect_ratio > 25: continue

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
    Professional preprocessing: CLAHE + Blur + Morphological Cleanup + Adaptive Threshold.
    Optimized for dense alphanumeric barcodes (Code128/Code39).
    """
    # 1. CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # 2. Horizontal Sharpening Kernel (Enhances vertical barcode lines)
    sharpen_kernel = np.array([[-1, 2, -1],
                               [-1, 2, -1],
                               [-1, 2, -1]])
    sharpened = cv2.filter2D(enhanced, -1, sharpen_kernel)
    enhanced = cv2.addWeighted(enhanced, 0.8, sharpened, 0.2, 0) # Blend slightly

    # 3. Gaussian Blur to reduce noise before thresholding
    blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)

    # 4. Adaptive Thresholding (Excellent for varying lighting on dense codes)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)

    # 5. Morphological Closing (helps repair broken barcode lines)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    return closed

def format_barcode_result(result):
    """
    ZXing natively expands UPC-E into a 13-digit EAN-13 representation.
    This safely compresses it back to the original 8-digit UPC-E string.
    """
    text = result.text
    if result.format.name == 'UPCE':
        if len(text) == 13 and text.startswith('0'):
            upca = text[1:]
            sys_d = upca[0]
            chk_d = upca[-1]
            mfg = upca[1:6]
            prd = upca[6:11]
            if mfg[-3:] in ['000', '100', '200'] and prd <= '00999':
                d = mfg[:2] + prd[-3:] + mfg[2]
            elif mfg[-2:] == '00' and prd <= '00099':
                d = mfg[:3] + prd[-2:] + '3'
            elif mfg[-1:] == '0' and prd <= '00009':
                d = mfg[:4] + prd[-1:] + '4'
            elif prd >= '00005' and prd <= '00009':
                d = mfg + prd[-1:]
            else:
                return text
            return sys_d + d + chk_d
    return text

def _decode_barcode_sync(image_base64: str):
    """
    Professional-grade scanning pipeline.
    Returns: (barcode_text, metadata_dict)
    """
    start_time = time.time()
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
        metadata["is_blurry"] = blur_score < 50 # Relaxed blur constraint for macros
        
        if metadata["is_blurry"]:
            return metadata

        # 2. Convert to Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 3. Direct Decoding
        results = zxingcpp.read_barcodes(gray)
        if results:
            metadata["barcode"] = format_barcode_result(results[0])
            return metadata

        # 3.5 Direct Decoding w/ GlobalHistogram (Helps highly shiny/reflective labels)
        results = zxingcpp.read_barcodes(gray, binarizer=zxingcpp.Binarizer.GlobalHistogram)
        if results:
            metadata["barcode"] = format_barcode_result(results[0])
            return metadata

        # 4. Advanced Preprocessing Pipeline (Adaptive Threshold, Sharpening)
        preprocessed = preprocess_for_high_accuracy(gray)
        results = zxingcpp.read_barcodes(preprocessed)
        if results:
            metadata["barcode"] = format_barcode_result(results[0])
            return metadata

        # 5. ROI Based Decoding (Targeted)
        rois = detect_roi(gray)
        # Limit to top 4 largest ROIs to prevent explosion of work
        for roi in rois[:4]:
            # Abort if we are taking too long overall
            if time.time() - start_time > 8.0: break
            
            # Try original and preprocessed ROI
            results = zxingcpp.read_barcodes(roi)
            if not results:
                roi_prep = preprocess_for_high_accuracy(roi)
                results = zxingcpp.read_barcodes(roi_prep)
            
            if results:
                metadata["barcode"] = format_barcode_result(results[0])
                print(f"DEBUG: Scanned via ROI in {time.time()-start_time:.3f}s")
                return metadata

        # 6. Final Resort: Upscale + Canny + Zxing (Only on central crop to save time)
        if time.time() - start_time < 10.0:
            h, w = gray.shape
            center_gray = gray[h//4:3*h//4, w//4:3*w//4]
            # Fast Linear interpolation
            upscaled = cv2.resize(center_gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_LINEAR)
            edges = cv2.Canny(upscaled, 100, 200)
            results = zxingcpp.read_barcodes(edges)
            if results:
                metadata["barcode"] = format_barcode_result(results[0])
                print(f"DEBUG: Scanned via Canny in {time.time()-start_time:.3f}s")
                return metadata

        # 7. Ultimate Fallback: The PyZbar Engine (Run on downscaled to avoid 10s hangs)
        if time.time() - start_time < 12.0:
            try:
                from pyzbar.pyzbar import decode as pyzbar_decode
                # Downscale for pyzbar if too large
                h, w = gray.shape
                if w > 640:
                    pyz_img = cv2.resize(gray, (640, int(h * 640/w)))
                else:
                    pyz_img = gray
                    
                pyz_results = pyzbar_decode(pyz_img)
                if pyz_results:
                    metadata["barcode"] = pyz_results[0].data.decode('utf-8')
                    print(f"DEBUG: Scanned via PyZbar in {time.time()-start_time:.3f}s")
                    return metadata
            except Exception:
                pass
            
        return metadata
    except Exception as e:
        print(f"Error in professional scanning pipeline: {e}")
        return metadata
    finally:
        elapsed = time.time() - start_time
        if elapsed > 1.0:
            print(f"WARNING: Barcode scan took {elapsed:.3f}s")

async def decode_barcode(image_base64: str):
    """Async wrapper for professional barcode decoding."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_decode_barcode_sync, image_base64))
