import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys
from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.jwt_utils import get_password_hash

load_dotenv()

async def reset_password():
    client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
    db = client.get_database()
    users_col = db.get_collection("users")
    
    email = "banipark@seller.com"
    new_password = "password123"
    hashed = get_password_hash(new_password)
    
    result = await users_col.update_one(
        {"email": email},
        {"$set": {"hashed_password": hashed}}
    )
    
    if result.modified_count > 0:
        print(f"✅ Successfully reset password for {email} to: {new_password}")
    else:
        # Check if user exists but password already matches or update failed
        user = await users_col.find_one({"email": email})
        if user:
            print(f"ℹ️ User {email} found, but no changes were made (password might already be reset).")
        else:
            print(f"❌ User {email} not found in database.")

if __name__ == "__main__":
    asyncio.run(reset_password())
