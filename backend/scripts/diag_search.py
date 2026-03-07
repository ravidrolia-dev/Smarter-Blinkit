import os
import sys
import asyncio
import json

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_products_collection
from services.semantic_search import rank_products_by_query
from services.product_generator import generate_search_products

async def diag_search():
    print("\n--- Smart Search Diagnostics ---")
    
    # 1. Check Database connection and product count
    products_col = get_products_collection()
    count = await products_col.count_documents({})
    print(f"Total products in DB: {count}")
    
    # 2. Test Semantic Search with diverse queries
    queries = ["I have a headache", "Milk", "Shampoo"]
    for query in queries:
        print(f"\nTesting Semantic Search for: '{query}'")
        
        cursor = products_col.find({"stock": {"$gt": 0}})
        products = await cursor.to_list(length=500)
        for p in products: p["id"] = str(p["_id"])
        
        results = rank_products_by_query(query, products)
        print(f"Semantic Search found {len(results)} matches for '{query}'.")
        if results:
            print(f"Top result: {results[0]['name']} (Score: {results[0]['_score']})")
    
    # 3. Test AI Product Generation (The part that likely fails)
    print(f"\nTesting AI Product Generation for: '{query}'")
    try:
        generated = await generate_search_products(query)
        print(f"AI Generation returned {len(generated)} products.")
        for p in generated:
            print(f" - {p['name']} ({p.get('category')})")
    except Exception as e:
        print(f"❌ AI Generation Failed: {e}")

if __name__ == "__main__":
    asyncio.run(diag_search())
