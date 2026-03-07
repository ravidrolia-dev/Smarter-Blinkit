import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_products_collection

load_dotenv()

async def list_unique_categories():
    products_col = get_products_collection()
    
    print("--- All Unique Categories and Counts ---")
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    cursor = products_col.aggregate(pipeline)
    async for doc in cursor:
        print(f"Category: {doc['_id']}, Count: {doc['count']}")

if __name__ == "__main__":
    asyncio.run(list_unique_categories())
