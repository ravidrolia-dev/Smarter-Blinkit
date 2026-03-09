import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import certifi

async def verify():
    load_dotenv()
    uri = os.getenv("MONGO_URI")
    print(f"Checking connection to: {uri[:20]}...")
    
    client = AsyncIOMotorClient(uri, tlsCAFile=certifi.where())
    db = client.get_default_database()
    
    print("Creating indexes...")
    await db.users.create_index([("location", "2dsphere")])
    await db.products.create_index([("location", "2dsphere")])
    await db.shops.create_index([("location", "2dsphere")])
    await db.product_demand.create_index([("location", "2dsphere")])
    await db.product_demand.create_index([("product_name", 1), ("status", 1)])
    
    print("✅ Indexes verified/created successfully.")

if __name__ == "__main__":
    asyncio.run(verify())
