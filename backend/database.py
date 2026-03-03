from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/smarter_blinkit")

# Async client (for FastAPI endpoints)
async_client = AsyncIOMotorClient(MONGO_URI)
async_db = async_client.smarter_blinkit

# Sync client (for startup tasks)
sync_client = MongoClient(MONGO_URI)
sync_db = sync_client.smarter_blinkit

# Collections
def get_users_collection():
    return async_db.users

def get_products_collection():
    return async_db.products

def get_orders_collection():
    return async_db.orders

def get_shops_collection():
    return async_db.shops

async def create_indexes():
    """Create all required indexes."""
    users = get_users_collection()
    products = get_products_collection()
    orders = get_orders_collection()
    shops = get_shops_collection()

    await users.create_index("email", unique=True)
    await products.create_index("barcode")
    await products.create_index("seller_id")
    await products.create_index([("location", "2dsphere")])
    await orders.create_index("buyer_id")
    await orders.create_index("seller_id")
    await shops.create_index([("location", "2dsphere")])

    print("✅ Database indexes created")
