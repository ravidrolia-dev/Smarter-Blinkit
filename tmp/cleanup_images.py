import requests
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
from dotenv import load_dotenv

load_dotenv("a:/console/Smarter-Blinkit/backend/.env")
MONGO_URI = os.getenv("MONGO_URI")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

async def check_image(url):
    if not url or not url.startswith("http"):
        return False
    try:
        # Use GET with a browser-like User-Agent and short timeout
        r = requests.get(url, headers=HEADERS, timeout=5, stream=True)
        return r.status_code == 200
    except:
        return False

async def cleanup():
    if not MONGO_URI:
        print("❌ MONGO_URI not found.")
        return

    client = AsyncIOMotorClient(MONGO_URI)
    db = client.smarter_blinkit
    products_col = db.products
    
    products = await products_col.find({}).to_list(length=2000)
    print(f"Auditing {len(products)} products...")
    
    deleted_count = 0
    to_delete = []
    
    for p in products:
        url = p.get("image_url")
        name = p.get("name")
        is_ok = await check_image(url)
        if not is_ok:
            print(f"🗑️ Deleting broken: {name} -> {url}")
            to_delete.append(p["_id"])
        
        if len(to_delete) >= 20:
            res = await products_col.delete_many({"_id": {"$in": to_delete}})
            deleted_count += res.deleted_count
            to_delete = []

    if to_delete:
        res = await products_col.delete_many({"_id": {"$in": to_delete}})
        deleted_count += res.deleted_count
        
    print(f"\n✨ Cleanup Complete! Removed {deleted_count} items. All remaining products have working images.")
    client.close()

if __name__ == "__main__":
    asyncio.run(cleanup())
