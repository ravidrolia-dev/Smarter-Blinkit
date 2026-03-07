import os
import sys
import asyncio

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_products_collection
from services.semantic_search import rank_products_by_query

async def test_search_logic():
    print("\n--- Testing Search Logic ---")
    products_col = get_products_collection()
    
    # 1. Search for a generic term like "Milk" or "Pizza"
    query = "Milk"
    print(f"Searching for: {query}")
    
    cursor = products_col.find({"stock": {"$gt": 0}})
    products = await cursor.to_list(length=500)
    for p in products: p["id"] = str(p["_id"])
    
    results = rank_products_by_query(query, products)
    print(f"Found {len(results)} results.")
    for p in results[:3]:
        print(f" - {p['name']} (Score: {p['_score']})")

    # 2. Check for the items we just generated for "headache"
    query = "headache"
    print(f"\nSearching for: {query}")
    results = rank_products_by_query(query, products)
    print(f"Found {len(results)} results.")
    for p in results[:5]:
        print(f" - {p['name']} (Score: {p['_score']})")

if __name__ == "__main__":
    asyncio.run(test_search_logic())
