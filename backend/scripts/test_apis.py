import requests
url = "https://dummyjson.com/products/search?q=shampoo"
print("Trying DummyJSON:", url)
try:
    r = requests.get(url, timeout=5)
    print("Status:", r.status_code)
    data = r.json()
    print("Data length:", len(data.get("products", [])))
    print(data.get("products")[0] if data.get("products") else "No products")
except Exception as e:
    print("Error:", e)
    
url2 = "https://api.upcitemdb.com/prod/trial/search?s=shampoo&match_mode=0&type=product"
print("\nTrying UPCItemDB:", url2)
try:
    r = requests.get(url2, timeout=5)
    print("Status:", r.status_code)
    data = r.json()
    print("Data length:", len(data.get("items", [])))
    print(data.get("items")[0] if data.get("items") else "No items")
except Exception as e:
    print("Error:", e)
