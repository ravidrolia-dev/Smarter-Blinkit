from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/smarter_blinkit")

import certifi

# Async client (for FastAPI endpoints) — lazily connected, non-blocking
# Async client with short timeout so connection failures fail fast
async_client = AsyncIOMotorClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=5000,
    tlsCAFile=certifi.where() # Provide explicit Windows CA certificates to avoid SSL handshakes drops
)
async_db = async_client.smarter_blinkit

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

    print("Database indexes created")
