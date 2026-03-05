import barcode
from barcode.writer import ImageWriter
import cv2
import zxingcpp

def test_format(fmt_name, value):
    try:
        if fmt_name == 'upce':
            print(f"python-barcode does not strictly support upce exactly, but let's test ITF first")
            
        BARCODE = barcode.get_barcode_class(fmt_name)
        my_barcode = BARCODE(value, writer=ImageWriter())
        filename = my_barcode.save(f"test_{fmt_name}")
        
        img = cv2.imread(filename)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Test Default
        res1 = zxingcpp.read_barcodes(gray)
        
        # Test All Formats
        formats_all = zxingcpp.BarcodeFormat.ITF | zxingcpp.BarcodeFormat.UPCE
        res2 = zxingcpp.read_barcodes(gray, formats=formats_all)

        print(f"--- {fmt_name.upper()} ---")
        print(f"Default: {'Success: ' + res1[0].text if res1 else 'Failed'}")
        print(f"Explicit: {'Success: ' + res2[0].text if res2 else 'Failed'}")
    except Exception as e:
        print(f"Error testing {fmt_name}: {e}")

test_format('itf', '12345678901234')
