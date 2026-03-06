import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_products_collection

load_dotenv()

async def fix_medical_categories():
    products_col = get_products_collection()
    print("Fixing medical item categories...")
    
    for i in range(1, 11):
        code = f"MED{i:03d}"
        res = await products_col.update_many(
            {"barcode": code},
            {"$set": {"category": "Health & Wellness"}}
        )
        print(f"Updated {code}: {res.modified_count} documents")

if __name__ == "__main__":
    asyncio.run(fix_medical_categories())
