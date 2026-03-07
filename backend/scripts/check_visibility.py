import os
import sys
import asyncio

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_products_collection

async def check_products():
    print("\n--- Product Visibility Check ---")
    products_col = get_products_collection()
    
    # 1. Total products
    total = await products_col.count_documents({})
    print(f"Total Products: {total}")
    
    # 2. In-stock products
    in_stock = await products_col.count_documents({"stock": {"$gt": 0}})
    print(f"In-stock Products: {in_stock}")
    
    # 3. Sample products
    print("\nSample In-stock Products:")
    cursor = products_col.find({"stock": {"$gt": 0}}).limit(5)
    async for p in cursor:
        print(f" - {p.get('name')} | Stock: {p.get('stock')} | Category: {p.get('category')}")
        
    # 4. Check categories
    print("\nTop 5 Categories:")
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    async for cat in products_col.aggregate(pipeline):
        print(f" - {cat['_id']}: {cat['count']}")

if __name__ == "__main__":
    asyncio.run(check_products())
