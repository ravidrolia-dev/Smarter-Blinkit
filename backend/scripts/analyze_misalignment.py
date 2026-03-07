import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_products_collection

load_dotenv()

async def analyze_misalignment():
    products_col = get_products_collection()
    BAD_URL = "https://images.unsplash.com/photo-1542838132-92c53300491e"
    
    pipeline = [
        {"$match": {"image_url": {"$regex": BAD_URL}}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]
    
    print("--- Distribution of 'Grocery Aisle' image by Category ---")
    cursor = products_col.aggregate(pipeline)
    async for doc in cursor:
        print(f"Category: {doc['_id']}, Count: {doc['count']}")

if __name__ == "__main__":
    asyncio.run(analyze_misalignment())
