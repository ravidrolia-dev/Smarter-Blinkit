import asyncio
import os
import sys
import requests
import random
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_products_collection

load_dotenv()

FALLBACK_IMAGE = "https://images.unsplash.com/photo-1542838132-92c53300491e?q=80&w=1000&auto=format&fit=crop"

def is_valid_image(url):
    if not url or not url.startswith("http"):
        return False
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code == 200 and "image" in response.headers.get("Content-Type", "").lower()
    except:
        return False

async def get_dummyjson_images():
    try:
        r = requests.get("https://dummyjson.com/products?limit=100", timeout=10)
        if r.status_code == 200:
            products = r.json().get("products", [])
            return [p["thumbnail"] for p in products if p.get("thumbnail")]
    except:
        pass
    return []

async def fix_images():
    products_col = get_products_collection()
    dummy_images = await get_dummyjson_images()
    
    cursor = products_col.find({"auto_imported": True})
    total_checked = 0
    fixed_count = 0
    
    async for product in cursor:
        total_checked += 1
        url = product.get("image_url", "")
        
        # Check if URL is broken or placeholder-like
        needs_fix = False
        if not url or "flaticon.com" in url or "example.com" in url:
            needs_fix = True
        elif not is_valid_image(url):
            needs_fix = True
            
        if needs_fix:
            new_url = FALLBACK_IMAGE
            if dummy_images:
                new_url = random.choice(dummy_images)
            
            await products_col.update_one(
                {"_id": product["_id"]},
                {"$set": {"image_url": new_url}}
            )
            fixed_count += 1
            print(f"  [✓] Fixed image for: {product.get('name')} (Barcode: {product.get('barcode')})")

    print(f"\nImage fix job complete!")
    print(f"Total checked: {total_checked}")
    print(f"Total fixed: {fixed_count}")

if __name__ == "__main__":
    asyncio.run(fix_images())
