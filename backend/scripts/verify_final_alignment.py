import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_products_collection

load_dotenv()

async def verify_final_alignment():
    products_col = get_products_collection()
    categories = ["Health & Wellness", "Smartphones", "Laptops", "Baby Products", "Dairy"]
    
    for cat in categories:
        print(f"\n--- Category: {cat} (First 5) ---")
        cursor = products_col.find({"category": cat}).limit(5)
        async for p in cursor:
            print(f"Name: {p.get('name')}, Image: {p.get('image_url')}")

if __name__ == "__main__":
    asyncio.run(verify_final_alignment())
