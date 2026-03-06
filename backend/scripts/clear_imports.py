import asyncio
import os
import sys
from dotenv import load_dotenv
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database import get_products_collection

load_dotenv()

async def clear():
    col = get_products_collection()
    res = await col.delete_many({"auto_imported": True})
    print(f"Deleted {res.deleted_count} previously auto-imported products.")
    
asyncio.run(clear())
