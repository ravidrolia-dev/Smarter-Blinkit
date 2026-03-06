import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_products_collection

load_dotenv()

async def diag():
    products_col = get_products_collection()
    cursor = products_col.find({"auto_imported": True})
    all_products = await cursor.to_list(length=2000)
    
    counts = {}
    for p in all_products:
        url = p.get("image_url", "")
        if not url:
            domain = "none"
        else:
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
            except:
                domain = "invalid"
        
        counts[domain] = counts.get(domain, 0) + 1
    
    print("\n--- Image Domains Statistics ---")
    for domain, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{domain}: {count}")

if __name__ == "__main__":
    asyncio.run(diag())
