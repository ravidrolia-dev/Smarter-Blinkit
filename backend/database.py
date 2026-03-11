from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/smarter_blinkit")

import certifi

try:
    async_client = AsyncIOMotorClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=5000,
        tlsCAFile=certifi.where() # Provide explicit Windows CA certificates to avoid SSL handshakes drops
    )
    # Database objects do not implement truth value testing, compare with None
    async_db = async_client.get_default_database()
    if async_db is None:
        async_db = async_client.smarter_blinkit
except Exception as e:
    print(f"CRITICAL: Failed to initialize MongoDB client: {e}")
    # Still define async_db to avoid NameError elsewhere, but it will fail on use
    async_db = None

# Collections
def get_users_collection():
    return async_db.users

def get_products_collection():
    return async_db.products

def get_orders_collection():
    return async_db.orders

def get_shops_collection():
    return async_db.shops

def get_product_demand_collection():
    return async_db.product_demand

def get_recipe_cache_collection():
    return async_db.recipe_cache

def get_product_reviews_collection():
    return async_db.product_reviews

def get_product_pairings_collection():
    return async_db.product_pairings

async def create_indexes():
    """Create all required indexes."""
    users = get_users_collection()
    products = get_products_collection()
    orders = get_orders_collection()
    shops = get_shops_collection()
    demand = get_product_demand_collection()
    recipe_cache = get_recipe_cache_collection()

    await users.create_index("email", unique=True)
    await products.create_index("barcode")
    await products.create_index("seller_id")
    await products.create_index([("location", "2dsphere")])
    await orders.create_index("buyer_id")
    await orders.create_index("seller_id")
    await shops.create_index([("location", "2dsphere")])
    
    # Demand & Cache indexes
    await demand.create_index([("product_name", 1), ("status", 1)])
    await demand.create_index([("location", "2dsphere")])
    await demand.create_index("status")
    await recipe_cache.create_index("meal_query", unique=True)
    
    # Review indexes
    reviews = get_product_reviews_collection()
    await reviews.create_index("product_id")
    await reviews.create_index("user_id")
    await reviews.create_index([("user_id", 1), ("product_id", 1), ("order_id", 1)], unique=True)

    print("Database indexes created")
