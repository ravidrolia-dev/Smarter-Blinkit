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

# --- HIGH QUALITY IMAGE LIBRARY ---
# These are guaranteed high-quality images for specific keywords
IMG_LIBRARY = {
    "bread": [
        "https://images.unsplash.com/photo-1509440159596-0249088772ff?q=80&w=1000&auto=format&fit=crop", # Brown Bread
        "https://images.unsplash.com/photo-1534620808146-d33bb39128b2?q=80&w=1000&auto=format&fit=crop", # Loaf
        "https://images.unsplash.com/photo-1598373182133-52452f7691ef?q=80&w=1000&auto=format&fit=crop"  # Sliced Bread
    ],
    "cookie": [
        "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?q=80&w=1000&auto=format&fit=crop", # Choco Cookie
        "https://images.unsplash.com/photo-1558961363-fa8fdf82db35?q=80&w=1000&auto=format&fit=crop"  # Cookies pile
    ],
    "milk": [
        "https://images.unsplash.com/photo-1563227812-0ea4c22e6cc8?q=80&w=1000&auto=format&fit=crop", # Milk bottle
        "https://images.unsplash.com/photo-1550583724-125581cc25db?q=80&w=1000&auto=format&fit=crop"  # Glass of milk
    ],
    "egg": [
        "https://images.unsplash.com/photo-1582722134903-b1297ade7995?q=80&w=1000&auto=format&fit=crop"  # Eggs tray
    ],
    "juice": [
        "https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?q=80&w=1000&auto=format&fit=crop"  # Orange Juice
    ],
    "soda": [
        "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?q=80&w=1000&auto=format&fit=crop"  # Cola/Coke
    ],
    "meat": [
        "https://images.unsplash.com/photo-1607623273562-b9e70f61284d?q=80&w=1000&auto=format&fit=crop"  # Raw meat
    ],
    "chicken": [
        "https://images.unsplash.com/photo-1604503468506-a8da13d82791?q=80&w=1000&auto=format&fit=crop"  # Chicken
    ],
    "paneer": [
        "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?q=80&w=1000&auto=format&fit=crop"  # Paneer/Tofu
    ]
}

async def fetch_dummyjson_groceries():
    print("--- Fetching DummyJSON Grocery Pool (STRICT) ---")
    grocery_pool = []
    personal_care_pool = []
    
    try:
        r = requests.get("https://dummyjson.com/products?limit=200", timeout=10)
        if r.status_code == 200:
            products = r.json().get("products", [])
            for p in products:
                cat = (p.get("category") or "").lower()
                img = p.get("thumbnail")
                if not img: continue
                
                # STRICT FILTERING
                if cat == "groceries":
                    grocery_pool.append({"title": p.get("title", ""), "url": img})
                elif cat in ["beauty", "fragrances", "skin-care"]:
                    personal_care_pool.append({"title": p.get("title", ""), "url": img})
                    
    except Exception as e:
        print(f"Error fetching DummyJSON: {e}")
    
    return grocery_pool, personal_care_pool

async def precision_image_fix():
    products_col = get_products_collection()
    groceries, personal_care = await fetch_dummyjson_groceries()
    
    cursor = products_col.find({"auto_imported": True})
    all_products = await cursor.to_list(length=2000)
    print(f"\nRevisiting {len(all_products)} products with Precision Matcher...")

    fixed_count = 0
    
    for product in all_products:
        name = product.get("name", "").lower()
        cat = product.get("category", "")
        
        # 1. Check for high-accuracy Keyword Library first (Bread, Cookie, etc.)
        new_url = None
        for kw, urls in IMG_LIBRARY.items():
            if kw in name:
                new_url = random.choice(urls)
                break
        
        # 2. If no direct keyword match, try DummyJSON title match
        if not new_url:
            pool = groceries if cat in ["Groceries", "Fruits & Vegetables", "Meats & Seafood", "Bakery & Cakes", "Beverages"] else personal_care
            for item in pool:
                if item["title"].lower() in name or name in item["title"].lower():
                    new_url = item["url"]
                    break
        
        # 3. If still no match, pick a RANDOM item from the SPECIFIC category pool (NO CROSS-POLLINATION)
        if not new_url:
            pool = groceries if cat in ["Groceries", "Fruits & Vegetables", "Meats & Seafood", "Bakery & Cakes", "Beverages"] else personal_care
            if pool:
                new_url = random.choice(pool)["url"]
            else:
                # Absolute last resort: Generic Grocery Aisle from Unsplash
                new_url = "https://images.unsplash.com/photo-1542838132-92c53300491e?q=80&w=1000&auto=format&fit=crop"

        # Update the product with the precise image
        await products_col.update_one(
            {"_id": product["_id"]},
            {"$set": {"image_url": new_url}}
        )
        fixed_count += 1
        if fixed_count % 50 == 0:
            print(f"  [✓] Processed {fixed_count} products...")

    print(f"\nPrecision Image Sync Complete!")
    print(f"Total updated: {fixed_count}")

if __name__ == "__main__":
    asyncio.run(precision_image_fix())
