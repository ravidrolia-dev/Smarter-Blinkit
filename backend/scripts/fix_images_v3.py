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

# High-quality fallback pool
FALLBACKS = [
    "https://images.unsplash.com/photo-1542838132-92c53300491e?q=80&w=1000&auto=format&fit=crop", # Grocery Aisle
    "https://images.unsplash.com/photo-1543168256-418811576931?q=80&w=1000&auto=format&fit=crop", # Fruits
    "https://images.unsplash.com/photo-1506484334402-40f24505f6d5?q=80&w=1000&auto=format&fit=crop", # Vegetables
    "https://images.unsplash.com/photo-1563227812-0ea4c22e6cc8?q=80&w=1000&auto=format&fit=crop", # Milk/Dairy
    "https://images.unsplash.com/photo-1582401656496-9d75f92807fb?q=80&w=1000&auto=format&fit=crop"  # Snacks
]

# Domains that frequently block hotlinking or are slow/dead
BAD_DOMAINS = ["m.media-amazon.com", "flaticon.com", "example.com", "dummyimage.com"]

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
                cat = p.get("category", "")
                img = p.get("thumbnail")
                if not img: continue
                
                # Simple mapping
                if "grocery" in cat.lower(): pools["Groceries"].append(img)
                elif "beverage" in cat.lower(): pools["Beverages"].append(img)
                elif "beauty" in cat.lower() or "fragrance" in cat.lower() or "skin" in cat.lower(): pools["Personal Care"].append(img)
                elif "furniture" in cat.lower() or "home" in cat.lower() or "kitchen" in cat.lower(): pools["Household"].append(img)
                elif "laptop" in cat.lower() or "phone" in cat.lower() or "watch" in cat.lower(): pools["Electronics"].append(img)
                else: pools["General"].append(img)
    except Exception as e:
        print(f"Error fetching DummyJSON pool: {e}")
    
    return pools

async def fix_images_v3():
    products_col = get_products_collection()
    pools = await get_dummyjson_pool()
    
    cursor = products_col.find({"auto_imported": True})
    all_products = await cursor.to_list(length=2000)
    print(f"\nProcessing {len(all_products)} products with FAST mode...")

    fixed_count = 0
    
    for product in all_products:
        url = product.get("image_url", "")
        name = product.get("name", "Unknown")
        cat = product.get("category", "General")
        
        # Aggressive check: if it's from a bad domain, just replace it
        needs_fix = False
        if not url:
            needs_fix = True
        else:
            for domain in BAD_DOMAINS:
                if domain in url:
                    needs_fix = True
                    break

        if needs_fix:
            # Pick from category pool if available, else general, else Unsplash
            pool = pools.get(cat, pools["General"])
            if not pool: pool = pools["General"]
            
            if pool:
                new_url = random.choice(pool)
            else:
                new_url = random.choice(FALLBACKS)
            
            await products_col.update_one(
                {"_id": product["_id"]},
                {"$set": {"image_url": new_url}}
            )
            fixed_count += 1
            if fixed_count % 10 == 0:
                print(f"  [✓] Fixed {fixed_count} images so far...")

    print(f"\nFinal Fast Update Job Complete!")
    print(f"Total fixed: {fixed_count}")

if __name__ == "__main__":
    asyncio.run(fix_images_v3())
