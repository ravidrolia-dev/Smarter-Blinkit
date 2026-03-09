import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_products_collection, get_users_collection
from services.recipe_agent import generate_mock_product

load_dotenv()

async def verify_supplementation():
    products_col = get_products_collection()
    users_col = get_users_collection()

    print("--- 1. Identifying Current Dominant Seller ---")
    pipeline = [
        {"$group": {"_id": "$seller_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]
    cursor = products_col.aggregate(pipeline)
    res = await cursor.to_list(length=1)
    
    if not res:
        print("No products found in DB. Cannot verify dominant seller.")
        return

    top_seller_id = res[0]["_id"]
    count = res[0]["count"]
    
    from bson import ObjectId
    try:
        seller = await users_col.find_one({"_id": ObjectId(top_seller_id)})
    except:
        seller = await users_col.find_one({"seller_id": top_seller_id})
        
    seller_name = seller.get("name") if seller else "Unknown"
    print(f"Dominant Seller: {seller_name} ({top_seller_id}) with {count} products.")

    print("\n--- 2. Verifying Seller Assignment Logic (with AI) ---")
    # This might fail due to quota, but we'll see the fallback in action
    new_product_ai = await generate_mock_product("Rare Saffron")
    if new_product_ai:
        print(f"Product: {new_product_ai['name']} | Seller: {new_product_ai['seller_name']}")

    print("\n--- 3. Verifying Rule-Based Fallback ---")
    # Force fallback by passing an invalid model
    new_product_fallback = await generate_mock_product("Organic Dragon Fruit", model_name="non-existent-model")
    
    if new_product_fallback:
        print(f"Fallback Product: {new_product_fallback['name']}")
        print(f"Assigned Seller Name: {new_product_fallback['seller_name']}")
        print(f"Category: {new_product_fallback['category']}")
        
        if str(new_product_fallback['seller_id']) == str(top_seller_id):
            print("\nSUCCESS: Fallback correctly assigned to the dominant seller!")
        else:
            print(f"\nFAILURE: Assigned to {new_product_fallback['seller_id']} instead of {top_seller_id}")
    else:
        print("\nFAILURE: Fallback failed to return a product.")

    print("\n[VERIFICATION COMPLETE]")

if __name__ == "__main__":
    asyncio.run(verify_supplementation())
