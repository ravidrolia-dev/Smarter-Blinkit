import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_products_collection

load_dotenv()

async def check_indian():
    products_col = get_products_collection()
    count = await products_col.count_documents({"barcode": {"$regex": "^IND"}})
    print(f"Total Indian items found: {count}")
    
    # List some
    cursor = products_col.find({"barcode": {"$regex": "^IND"}}).limit(5)
    async for p in cursor:
        print(f"Found {p.get('barcode')}: {p.get('name')}")

if __name__ == "__main__":
    asyncio.run(check_indian())
