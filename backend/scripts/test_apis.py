import os
import sys
import asyncio
import json

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routes.products import list_products
from routes.search import smart_search

async def test_api():
    print("\n=== API Endpoint Testing ===")
    
    # 1. Test /products
    print("\n[1] Testing /products (Dashboard list)")
    try:
        res = await list_products(limit=8)
        print(f"Returned {len(res)} products.")
        if res:
            print(f"First product: {res[0]['name']} (ID: {res[0]['id']})")
    except Exception as e:
        print(f"❌ /products Failed: {e}")

    # 2. Test /search?q=Headache
    print("\n[2] Testing /search?q=Headache")
    try:
        res = await smart_search(q="Headache", lat=None, lng=None, limit=5)
        print(f"Returned {res['count']} results.")
        for r in res['results'][:3]:
            print(f" - {r['name']} (Score: {r.get('_score')})")
    except Exception as e:
        print(f"❌ /search Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())
