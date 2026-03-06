import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_products_collection

load_dotenv()

async def check_fresh():
    products_col = get_products_collection()
    count = await products_col.count_documents({"barcode": {"$regex": "^FRE"}})
    print(f"Total Fresh items (FRE) found: {count}")
    
    # List some
    cursor = products_col.find({"barcode": {"$regex": "^FRE"}}).limit(10)
    async for p in cursor:
        print(f"Found {p.get('barcode')} ({p.get('seller_name')}): {p.get('name')} | Cat: {p.get('category')}")

if __name__ == "__main__":
    asyncio.run(check_fresh())
