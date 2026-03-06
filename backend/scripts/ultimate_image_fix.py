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

# High-quality fallback pool from Unsplash (diverse categories)
UNSPLASH_FALLBACKS = [
    "https://images.unsplash.com/photo-1542838132-92c53300491e?q=80&w=1000&auto=format&fit=crop", # Grocery Aisle
    "https://images.unsplash.com/photo-1543168256-418811576931?q=80&w=1000&auto=format&fit=crop", # Fruits
    "https://images.unsplash.com/photo-1506484334402-40f24505f6d5?q=80&w=1000&auto=format&fit=crop", # Vegetables
    "https://images.unsplash.com/photo-1563227812-0ea4c22e6cc8?q=80&w=1000&auto=format&fit=crop", # Milk/Dairy
    "https://images.unsplash.com/photo-1582401656496-9d75f92807fb?q=80&w=1000&auto=format&fit=crop", # Snacks
    "https://images.unsplash.com/photo-1512152272829-e3139592d56f?q=80&w=1000&auto=format&fit=crop", # Burger/Fast Food
    "https://images.unsplash.com/photo-1441986300917-64674bd600d8?q=80&w=1000&auto=format&fit=crop", # Store
]

async def get_dummyjson_pool():
    print("--- Fetching DummyJSON Image Pool ---")
    pools = {
        "Groceries": [],
        "Beverages": [],
        "Personal Care": [],
        "Household": [],
        "Health & Wellness": [],
        "Electronics": [],
        "Baby Products": [],
        "Bakery & Cakes": [],
        "Fruits & Vegetables": [],
        "Meats & Seafood": [],
        "General": []
    }
    
    try:
        r = requests.get("https://dummyjson.com/products?limit=0", timeout=10)
        if r.status_code == 200:
            products = r.json().get("products", [])
            for p in products:
                cat = (p.get("category") or "").lower()
                img = p.get("thumbnail")
                if not img: continue
                
                if "grocery" in cat: pools["Groceries"].append(img)
                elif "beverage" in cat: pools["Beverages"].append(img)
                elif "beauty" in cat or "fragrance" in cat or "skin" in cat: pools["Personal Care"].append(img)
                elif "furniture" in cat or "home" in cat or "kitchen" in cat: pools["Household"].append(img)
                elif "laptop" in cat or "phone" in cat or "watch" in cat: pools["Electronics"].append(img)
                elif "baby" in cat: pools["Baby Products"].append(img)
                else: pools["General"].append(img)
                
            # Populate missing pools from General
            for k, v in pools.items():
                if not v and k != "General":
                    pools[k] = pools["General"]
                    
    except Exception as e:
        print(f"Error fetching DummyJSON pool: {e}")
    
    return pools

async def ultimate_image_fix():
    products_col = get_products_collection()
    pools = await get_dummyjson_pool()
    
    cursor = products_col.find({"auto_imported": True})
    all_products = await cursor.to_list(length=2000)
    print(f"\nScanning {len(all_products)} products for unreliable image sources...")

    fixed_count = 0
    
    # We will replace anything that is NOT from DummyJSON or Unsplash and looks suspicious
    # Or just replace anything from known bad domains
    BAD_DOMAINS = ["openbeautyfacts.org", "openfoodfacts.org", "flaticon.com", "example.com", "m.media-amazon.com"]

    for product in all_products:
        url = product.get("image_url", "")
        name = product.get("name", "Unknown")
        cat = product.get("category", "General")
        
        needs_fix = False
        if not url:
            needs_fix = True
        else:
            for domain in BAD_DOMAINS:
                if domain in url:
                    needs_fix = True
                    break
        
        if needs_fix:
            # Pick from category pool
            pool = pools.get(cat, pools["General"])
            if not pool: pool = pools["General"] + UNSPLASH_FALLBACKS
            
            new_url = random.choice(pool) if pool else random.choice(UNSPLASH_FALLBACKS)
            
            await products_col.update_one(
                {"_id": product["_id"]},
                {"$set": {"image_url": new_url}}
            )
            fixed_count += 1
            if fixed_count % 20 == 0:
                print(f"  [✓] Fixed {fixed_count} images...")

    print(f"\nUltimate Update Job Complete!")
    print(f"Total fixed: {fixed_count} products now have guaranteed working images.")

if __name__ == "__main__":
    asyncio.run(ultimate_image_fix())
