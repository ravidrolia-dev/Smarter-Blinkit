import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64

try:
    UPCA = barcode.get_barcode_class('upca')
    base_code = "12345600001"
    upc_code = UPCA(base_code, writer=ImageWriter())
    
    options = {
        'module_width': 0.3,
        'module_height': 15.0,
        'quiet_zone': 6.0,
        'font_size': 12,
        'text_distance': 4.0,
        'format': 'PNG'
    }
    
    buffer = BytesIO()
    upc_code.write(buffer, options=options)
    print("Success")
except Exception as e:
    print(f"Error: {repr(e)}")
