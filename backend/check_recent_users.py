from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def check_recent_users():
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/smarter_blinkit")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.smarter_blinkit
    users_col = db.users
    
    print(f"Checking most recent users in {MONGO_URI}...")
    # Sort by _id descending to get newest first
    cursor = users_col.find({}).sort("_id", -1).limit(5)
    users = await cursor.to_list(length=5)
    
    if not users:
        print("No users found in database.")
        return

    for u in users:
        email = u.get('email')
        name = u.get('name')
        enc = u.get('face_encoding')
        has_enc = "YES" if enc else "NULL"
        enc_len = len(enc) if enc else 0
        print(f"User: {email} ({name}), Encoding: {has_enc}, Length: {enc_len}")

if __name__ == "__main__":
    asyncio.run(check_recent_users())
