import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_products_collection

load_dotenv()

async def analyze_beauty_images():
    products_col = get_products_collection()
    beauty_cats = ["Beauty", "Skin-Care", "Fragrances", "Personal Care"]
    
    print("--- Beauty Product Image Analysis ---")
    for cat in beauty_cats:
        print(f"\nCategory: {cat}")
        pipeline = [
            {"$match": {"category": cat}},
            {"$group": {
                "_id": None,
                "total": {"$sum": 1},
                "dummyjson": {"$sum": {"$cond": [{"$regexMatch": {"input": "$image_url", "regex": "dummyjson.com"}}, 1, 0]}},
                "unsplash": {"$sum": {"$cond": [{"$regexMatch": {"input": "$image_url", "regex": "unsplash.com"}}, 1, 0]}},
                "obf": {"$sum": {"$cond": [{"$regexMatch": {"input": "$image_url", "regex": "openbeautyfacts.org"}}, 1, 0]}},
                "other": {"$sum": {"$cond": [{"$not": [{"$or": [
                    {"$regexMatch": {"input": "$image_url", "regex": "dummyjson.com"}},
                    {"$regexMatch": {"input": "$image_url", "regex": "unsplash.com"}},
                    {"$regexMatch": {"input": "$image_url", "regex": "openbeautyfacts.org"}}
                ]}]}, 1, 0]}}
            }}
        ]
        cursor = products_col.aggregate(pipeline)
        async for doc in cursor:
            print(f"  Total: {doc['total']}")
            print(f"  DummyJSON: {doc['dummyjson']}")
            print(f"  Unsplash: {doc['unsplash']}")
            print(f"  OpenBeautyFacts: {doc['obf']}")
            print(f"  Other: {doc['other']}")

if __name__ == "__main__":
    asyncio.run(analyze_beauty_images())
