import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_products_collection

load_dotenv()

async def analyze_full_misalignment():
    products_col = get_products_collection()
    
    # List of all broad Unsplash URLs used as fallbacks
    BROAD_URLS = {
        "https://images.unsplash.com/photo-1542838132-92c53300491e": "Groceries",
        "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd": "Beverages",
        "https://images.unsplash.com/photo-1556228720-195a672e8a03": "Personal Care",
        "https://images.unsplash.com/photo-1498049794561-7780e7231661": "Electronics",
        "https://images.unsplash.com/photo-1581578731548-c64695cc6954": "Household",
        "https://images.unsplash.com/photo-1610348725531-843dff563e2c": "Fruits & Vegetables",
        "https://images.unsplash.com/photo-1607623273562-b9e70f61284d": "Meats & Seafood",
        "https://images.unsplash.com/photo-1509440159596-0249088772ff": "Bakery & Cakes",
    }
    
    print("--- Detailed Category-Image Analysis ---")
    for url, original_cat in BROAD_URLS.items():
        print(f"\nImage: {url} (Intended for: {original_cat})")
        pipeline = [
            {"$match": {"image_url": {"$regex": url}}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}}
        ]
        cursor = products_col.aggregate(pipeline)
        async for doc in cursor:
            # Only print if the category doesn't match roughly the intended category
            if doc['_id'] != original_cat:
                print(f"  !! MISMATCH !! Category: {doc['_id']}, Count: {doc['count']}")
            else:
                print(f"  OK: Category: {doc['_id']}, Count: {doc['count']}")

if __name__ == "__main__":
    asyncio.run(analyze_full_misalignment())
