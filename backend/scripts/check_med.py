import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_products_collection

load_dotenv()

async def check_medical():
    products_col = get_products_collection()
    print("Checking medical items...")
    
    for i in range(1, 11):
        code = f"MED{i:03d}"
        p = await products_col.find_one({"barcode": code})
        if p:
            print(f"Found {code}: Name='{p.get('name')}', Price={p.get('price')}, Cat='{p.get('category')}'")
        else:
            print(f"Not found {code}")

if __name__ == "__main__":
    asyncio.run(check_medical())
