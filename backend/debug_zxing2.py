import zxingcpp
try:
    f = zxingcpp.BarcodeFormat.Code128
    print("Found in BarcodeFormat:")
    print(f)
except AttributeError:
    pass

try:
    f = zxingcpp.Code128
    print("Found in zxingcpp:")
    print(f)
except AttributeError:
    pass
