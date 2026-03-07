import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def debug_users():
    client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
    db = client.get_database()
    users_col = db.get_collection("users")
    
    sellers = await users_col.find({"role": "seller"}).to_list(length=10)
    print(f"Total sellers in sample: {len(sellers)}")
    for s in sellers:
        print(f"Name: {s.get('name')}, Location: {s.get('location')}")

if __name__ == "__main__":
    asyncio.run(debug_users())
