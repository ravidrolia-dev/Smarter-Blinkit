"""Check broken URLs and save to file"""
import requests
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["smarter_blinkit"]

products = list(db.products.find({}))
broken = []

for p in products:
    url = p.get("image_url", "")
    if not url:
        broken.append({"name": p["name"], "id": str(p["_id"]), "reason": "No URL"})
        continue
    
    try:
        r = requests.head(url, timeout=5, allow_redirects=True)
        if r.status_code != 200:
            broken.append({"name": p["name"], "id": str(p["_id"]), "url": url, "status": r.status_code})
    except Exception as e:
        broken.append({"name": p["name"], "id": str(p["_id"]), "url": url, "error": str(e)[:50]})

with open("broken_images.txt", "w") as f:
    f.write(f"Total products: {len(products)}\n")
    f.write(f"Broken images: {len(broken)}\n\n")
    
    if broken:
        f.write("BROKEN PRODUCTS:\n")
        f.write("="*50 + "\n")
        for item in broken:
            f.write(f"\nProduct: {item['name']}\n")
            f.write(f"ID: {item['id']}\n")
            if 'url' in item:
                f.write(f"URL: {item['url']}\n")
            if 'status' in item:
                f.write(f"Status: {item['status']}\n")
            if 'error' in item:
                f.write(f"Error: {item['error']}\n")
    else:
        f.write("All images working!\n")

print(f"Results saved to broken_images.txt")
print(f"Total: {len(products)}, Broken: {len(broken)}")

client.close()
