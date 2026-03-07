import asyncio
import os
import sys
import requests
import time
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_products_collection

load_dotenv()

OBF_SEARCH_API = "https://world.openbeautyfacts.org/cgi/search.pl"
HEADERS = {
    "User-Agent": "SmarterBlinkit/1.0 (contact@smarterblinkit.com)"
}

def is_valid_image(url):
    """Check if URL returns a valid image."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=8, stream=True, allow_redirects=True)
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '').lower()
            return 'image' in content_type
    except:
        pass
    return False

def search_obf(name):
    """Search OpenBeautyFacts by product name."""
    # Clean name for better search results
    search_name = name.split("(")[0].strip()
    
    params = {
        "search_terms": search_name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 10
    }
    
    try:
        r = requests.get(OBF_SEARCH_API, params=params, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            products = r.json().get("products", [])
            for p in products:
                # Prioritize front image, then any image
                img = p.get("image_front_url") or p.get("image_url") or p.get("image_small_url")
                if img and is_valid_image(img):
                    return img
    except Exception as e:
        print(f"      OBF Search error for '{search_name}': {e}")
    return None

async def fix_beauty_images(dry_run=False):
    products_col = get_products_collection()
    beauty_cats = ["Beauty", "Skin-Care", "Fragrances", "Personal Care"]
    
    query = {"category": {"$in": beauty_cats}}
    total = await products_col.count_documents(query)
    
    print(f"\n--- OpenBeautyFacts Beauty Image Fixer ---")
    if dry_run: print("!!! DRY RUN MODE !!!")
    print(f"Targeting {total} products in categories: {', '.join(beauty_cats)}")
    
    fixed_count = 0
    skipped_count = 0
    
    cursor = products_col.find(query)
    async for product in cursor:
        name = product.get("name", "").strip()
        print(f"🔍 Processing: {name}...", end=" ", flush=True)
        
        new_url = search_obf(name)
        
        if new_url:
            if not dry_run:
                await products_col.update_one(
                    {"_id": product["_id"]},
                    {"$set": {"image_url": new_url}}
                )
            print(f"[✓] Found: {new_url[:50]}...")
            fixed_count += 1
        else:
            print(f"[✗] Not found in OBF")
            skipped_count += 1
            
        await asyncio.sleep(0.5)

    print(f"\nBeauty Fix Job Complete!")
    print(f"Total Fixed from OBF: {fixed_count}")
    print(f"Total Skipped: {skipped_count}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    asyncio.run(fix_beauty_images(dry_run=args.dry_run))
