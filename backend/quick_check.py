"""Quick check for broken image URLs"""
import requests
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["smarter_blinkit"]

products = list(db.products.find({}))
broken = []

print(f"Checking {len(products)} products...")

for p in products:
    url = p.get("image_url", "")
    if not url:
        broken.append(p["name"])
        continue
    
    try:
        r = requests.head(url, timeout=3, allow_redirects=True)
        if r.status_code != 200:
            broken.append(p["name"])
            print(f"BROKEN: {p['name']}")
    except:
        broken.append(p["name"])
        print(f"BROKEN: {p['name']}")

print(f"\n\nTotal broken: {len(broken)}")
print("Broken products:", broken)

client.close()
