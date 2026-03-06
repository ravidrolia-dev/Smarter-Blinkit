import asyncio
import os
import sys
from dotenv import load_dotenv
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database import get_products_collection

load_dotenv()

async def debug():
    col = get_products_collection()
    count = await col.count_documents({})
    print("Total products:", count)
    seller_counts = {}
    async for p in col.find({}):
        seller_counts[p.get("seller_name", "Unknown")] = seller_counts.get(p.get("seller_name", "Unknown"), 0) + 1
    print("Sellers:", seller_counts)

asyncio.run(debug())
