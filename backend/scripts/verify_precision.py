import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_products_collection

load_dotenv()

async def verify():
    products_col = get_products_collection()
    
    keywords = ["Bread", "Cookie", "Milk", "Juice", "Chicken"]
    print(f"--- Verifying Image Accuracy for Keywords: {keywords} ---")
    
    for kw in keywords:
        print(f"\nChecking: {kw}")
        cursor = products_col.find({"name": {"$regex": kw, "$options": "i"}}, {"name": 1, "image_url": 1}).limit(3)
        async for p in cursor:
            print(f"  [PRODUCT] {p.get('name')}")
            print(f"  [IMAGE  ] {p.get('image_url')}")

if __name__ == "__main__":
    asyncio.run(verify())
