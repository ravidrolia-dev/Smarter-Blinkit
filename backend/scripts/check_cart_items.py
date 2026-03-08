import asyncio
import sys
import os
from bson import ObjectId

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_products_collection, get_users_collection

async def check_cart_items():
    products_col = get_products_collection()
    users_col = get_users_collection()
    
    # Items from user's screenshot
    queries = ["Eyeshadow Palette", "Lipstick"]
    
    for q in queries:
        print(f"\n🔍 Searching for: '{q}'")
        products = await products_col.find({"name": {"$regex": q, "$options": "i"}}).to_list(10)
        
        if not products:
            print("   ❌ No products found.")
            continue
            
        for p in products:
            seller_id = p.get("seller_id")
            seller = await users_col.find_one({"_id": ObjectId(seller_id)})
            has_loc = "Yes" if seller and "location" in seller else "No"
            coords = seller.get("location", {}).get("coordinates", []) if has_loc == "Yes" else []
            print(f"   - Name: {p['name']}")
            print(f"     Shop: {seller.get('name')} (ID: {seller_id})")
            print(f"     Stock: {p['stock']}")
            print(f"     Has Location: {has_loc} {coords}")

if __name__ == "__main__":
    asyncio.run(check_cart_items())
