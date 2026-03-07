import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_products_collection

load_dotenv()

async def check_categories():
    products_col = get_products_collection()
    categories = ["Electronics", "Health & Wellness", "Beauty", "Personal Care"]
    
    for cat in categories:
        print(f"\n--- Products in Category: {cat} (First 10) ---")
        cursor = products_col.find({"category": cat}).limit(10)
        async for product in cursor:
            print(f"Name: {product.get('name')}, Image: {product.get('image_url')}")

if __name__ == "__main__":
    asyncio.run(check_categories())
