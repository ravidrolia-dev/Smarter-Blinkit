from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def check_users():
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/smarter_blinkit")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.smarter_blinkit
    users_col = db.users
    
    print(f"Checking users in {MONGO_URI}...")
    cursor = users_col.find({})
    users = await cursor.to_list(length=100)
    
    if not users:
        print("No users found.")
        return

    for u in users:
        print(f"User: {u.get('email')}, Role: {u.get('role')}, Name: {u.get('name')}")

if __name__ == "__main__":
    asyncio.run(check_users())
