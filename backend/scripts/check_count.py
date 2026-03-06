import asyncio
import os
from dotenv import load_dotenv
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database import get_products_collection

load_dotenv()

async def check():
    col = get_products_collection()
    count = await col.count_documents({"auto_imported": True})
    print(f"Total auto_imported products: {count}")
    
asyncio.run(check())
