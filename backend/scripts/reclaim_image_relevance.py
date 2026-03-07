import asyncio
import os
import sys
import requests
import random
import time
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_products_collection

load_dotenv()

# Public Search APIs
OFF_SEARCH_API = "https://world.openfoodfacts.org/cgi/search.pl"
OBF_SEARCH_API = "https://world.openbeautyfacts.org/cgi/search.pl"

HEADERS = {
    "User-Agent": "SmarterBlinkit/1.0 (contact@smarterblinkit.com)"
}

# Unsplash images to avoid (the aisles we assigned)
BROAD_UNSPLASH_URLS = [
    "https://images.unsplash.com/photo-1542838132-92c53300491e", # Grocery Aisle
    "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd", # Beverages
    "https://images.unsplash.com/photo-1556228720-195a672e8a03", # Personal Care
    "https://images.unsplash.com/photo-1498049794561-7780e7231661", # Electronics
    "https://images.unsplash.com/photo-1581578731548-c64695cc6954", # Household
    "https://images.unsplash.com/photo-1610348725531-843dff563e2c", # Fruits & Vegetables
    "https://images.unsplash.com/photo-1607623273562-b9e70f61284d", # Meats & Seafood
    "https://images.unsplash.com/photo-1509440159596-0249088772ff", # Bakery & Cakes
]

def is_valid_image(url):
    """Check if URL returns a valid image."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=8, stream=True, allow_redirects=True)
        return response.status_code == 200 and 'image' in response.headers.get('Content-Type', '').lower()
    except:
        return False

def get_dummyjson_map():
    """Build a title -> thumbnail map from DummyJSON."""
    dummy_map = {}
    try:
        # Fetch up to 1000 dummy products to be sure
        r = requests.get("https://dummyjson.com/products?limit=1000", timeout=10)
        if r.status_code == 200:
            for p in r.json().get("products", []):
                title = p.get("title", "").strip().lower()
                dummy_map[title] = {
                    "thumbnail": p.get("thumbnail"),
                    "category": p.get("category")
                }
    except Exception as e:
        print(f"Error fetching DummyJSON map: {e}")
    return dummy_map

async def reclaim_relevance(dry_run=False):
    products_col = get_products_collection()
    dummy_map = get_dummyjson_map()
    
    # Process products that might have broad unsplash images
    # Or everything to ensure category correction
    cursor = products_col.find({"auto_imported": True})
    total = await products_col.count_documents({"auto_imported": True})
    
    print(f"\n--- Reclaiming Relevance for {total} Products ---")
    if dry_run: print("!!! DRY RUN !!!")
    
    reclaimed_count = 0
    cat_corrected_count = 0
    
    async for product in cursor:
        name = product.get("name", "").strip()
        name_lower = name.lower()
        current_img = product.get("image_url", "")
        current_cat = product.get("category", "")
        
        needs_image_fix = False
        # If it's one of the broad unsplash images we assigned
        for broad_url in BROAD_UNSPLASH_URLS:
            if broad_url in current_img:
                needs_image_fix = True
                break
        
        # Also check for category correction
        new_cat = current_cat
        new_img = current_img
        
        # Look up in DummyJSON map
        if name_lower in dummy_map:
            dummy_data = dummy_map[name_lower]
            # 1. Category Correction
            mapped_cat = dummy_data["category"].title()
            if mapped_cat != current_cat:
                new_cat = mapped_cat
                cat_corrected_count += 1
            
            # 2. Image Fix (if needed)
            if needs_image_fix:
                dummy_thumb = dummy_data["thumbnail"]
                if dummy_thumb:
                    new_img = dummy_thumb
                    reclaimed_count += 1
        else:
            # If not in DummyJSON, but it's a broad image, try a specific search based on corrected context
            if needs_image_fix:
                # We can't do complex search here efficiently for all, 
                # but we can try to guess a better keyword-based image if possible
                pass

        if new_cat != current_cat or new_img != current_img:
            if not dry_run:
                await products_col.update_one(
                    {"_id": product["_id"]},
                    {"$set": {"category": new_cat, "image_url": new_img}}
                )
            # print(f"Fixed: {name} (Cat: {current_cat}->{new_cat}, Img Reclaimed: {new_img != current_img})")

    print(f"\nReclaiming Complete!")
    print(f"Categories Corrected: {cat_corrected_count}")
    print(f"Images Reclaimed from DummyJSON: {reclaimed_count}")

if __name__ == "__main__":
    asyncio.run(reclaim_relevance())
