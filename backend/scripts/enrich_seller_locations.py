import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def enrich_sellers():
    client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
    db = client.get_database()
    users_col = db.get_collection("users")
    products_col = db.get_collection("products")
    
    sellers = await users_col.find({"role": "seller"}).to_list(length=100)
    print(f"Enriching {len(sellers)} sellers...")
    
    for s in sellers:
        seller_id = str(s["_id"])
        # Find first product with a location
        product = await products_col.find_one({
            "seller_id": seller_id,
            "location": {"$ne": None}
        })
        
        if product and "location" in product:
            loc = product["location"]
            await users_col.update_one(
                {"_id": s["_id"]},
                {"$set": {"location": loc}}
            )
            print(f"  ✅ Updated {s['name']} with location {loc['coordinates']}")
        else:
            # Fallback to Jaipur center if no products found
            # Jaipur Center: 26.9124, 75.7873
            fallback_loc = {"type": "Point", "coordinates": [75.7873, 26.9124]}
            await users_col.update_one(
                {"_id": s["_id"]},
                {"$set": {"location": fallback_loc}}
            )
            print(f"  ⚠️ Fallback location for {s['name']}")

    # Create index
    await users_col.create_index([("location", "2dsphere")])
    print("\n✅ Seller locations enriched and 2dsphere index created.")

if __name__ == "__main__":
    asyncio.run(enrich_sellers())
