import sys
import base64
from services.scanner_service import _decode_barcode_sync

def test(path):
    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    res = _decode_barcode_sync(b64)
    print(res)

if __name__ == "__main__":
    test(sys.argv[1])
