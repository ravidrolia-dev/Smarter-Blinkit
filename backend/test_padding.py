import cv2
import zxingcpp
import sys

img = cv2.imread(sys.argv[1])
if img is not None:
    padded = cv2.copyMakeBorder(img, 50, 50, 50, 50, cv2.BORDER_CONSTANT, value=[255, 255, 255])
    
    # Also test just standard binarizer
    gray = cv2.cvtColor(padded, cv2.COLOR_BGR2GRAY)
    
    results = zxingcpp.read_barcodes(gray)
    if results:
        print(f"Padded Success: {results[0].text}")
    else:
        print("Padded Failed")
        
    # Test stretching horizontally
    stretched = cv2.resize(gray, (0,0), fx=2.0, fy=1.0)
    results2 = zxingcpp.read_barcodes(stretched)
    if results2:
        print(f"Stretched Success: {results2[0].text}")
    else:
        print("Stretched Failed")
