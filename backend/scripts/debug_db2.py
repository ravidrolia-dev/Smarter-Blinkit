
import asyncio
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database import get_products_collection
from dotenv import load_dotenv

load_dotenv()

async def debug():
    col = get_products_collection()
    count = await col.count_documents({})
    auto = await col.count_documents({"auto_imported": True})
    print(f"Total products: {count}, Auto imported: {auto}")

    seller_counts = {}
    async for p in col.find({"auto_imported": True}):
        s_name = p.get("seller_name", "Unknown")
        seller_counts[s_name] = seller_counts.get(s_name, 0) + 1
        
    print("Auto imported by seller:", seller_counts)

    print("\n--- Product Samples ---")
    async for p in col.find({"auto_imported": True}).limit(3):
        print(f"Name: {p.get('name')}, Category: {p.get('category')}, Barcode: {p.get('barcode')}, Image: {p.get('image_url')}")

asyncio.run(debug())
