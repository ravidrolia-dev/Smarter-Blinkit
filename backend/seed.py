"""
Seed script — populates MongoDB with demo products, users, and shops.
Run: python seed.py
Make sure backend .env is configured with MONGO_URI.
"""
from pymongo import MongoClient
from passlib.context import CryptContext
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/smarter_blinkit"))
db = client.smarter_blinkit

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Clear collections
db.users.drop()
db.products.drop()
db.shops.drop()

print("🌱 Seeding users...")

# Demo users
buyer = {
    "email": "buyer@demo.com",
    "name": "Ravi Sharma",
    "role": "buyer",
    "phone": "+91 98765 43210",
    "hashed_password": pwd_context.hash("demo1234"),
    "face_encoding": None,
    "is_active": True,
}
seller1 = {
    "email": "seller@demo.com",
    "name": "Mumbai Fresh Mart",
    "role": "seller",
    "phone": "+91 91234 56789",
    "hashed_password": pwd_context.hash("demo1234"),
    "face_encoding": None,
    "is_active": True,
}
seller2 = {
    "email": "seller2@demo.com",
    "name": "Quick Grocers",
    "role": "seller",
    "phone": "+91 99887 76655",
    "hashed_password": pwd_context.hash("demo1234"),
    "face_encoding": None,
    "is_active": True,
}

buyer_id = db.users.insert_one(buyer).inserted_id
seller1_id = db.users.insert_one(seller1).inserted_id
seller2_id = db.users.insert_one(seller2).inserted_id
print(f"  ✅ Buyer: buyer@demo.com / demo1234")
print(f"  ✅ Seller 1: seller@demo.com / demo1234")
print(f"  ✅ Seller 2: seller2@demo.com / demo1234")

print("🌱 Seeding products...")

# Mumbai coordinates (demo)
MUMBAI_LAT, MUMBAI_LNG = 19.0760, 72.8777
PUNE_LAT, PUNE_LNG = 18.5204, 73.8567

products = [
    {"name": "Organic Honey", "description": "Pure natural honey with healing properties, great for sore throat and cold", "price": 299, "category": "Health", "barcode": "8901234567890", "stock": 50, "unit": "bottle", "tags": ["honey", "cold remedy", "organic", "natural", "health"], "seller_id": str(seller1_id), "seller_name": "Mumbai Fresh Mart", "location": {"type": "Point", "coordinates": [MUMBAI_LNG, MUMBAI_LAT]}, "rating": 4.8, "total_sold": 142},
    {"name": "Ginger Tea Bags", "description": "Spicy ginger tea for cold, cough, and immunity boost", "price": 120, "category": "Beverages", "barcode": "8901234567891", "stock": 80, "unit": "box", "tags": ["tea", "ginger", "cold remedy", "immunity", "herbal"], "seller_id": str(seller1_id), "seller_name": "Mumbai Fresh Mart", "location": {"type": "Point", "coordinates": [MUMBAI_LNG, MUMBAI_LAT]}, "rating": 4.6, "total_sold": 98},
    {"name": "Tulsi Drops", "description": "Ayurvedic tulsi extract for cold, fever, and respiratory issues", "price": 180, "category": "Health", "barcode": "8901234567892", "stock": 30, "unit": "bottle", "tags": ["tulsi", "herbal", "cold", "fever", "ayurvedic"], "seller_id": str(seller1_id), "seller_name": "Mumbai Fresh Mart", "location": {"type": "Point", "coordinates": [MUMBAI_LNG, MUMBAI_LAT]}, "rating": 4.5, "total_sold": 67},
    {"name": "Whole Wheat Flour", "description": "Fine ground whole wheat atta for making rotis, pizza dough, and bread", "price": 89, "category": "Bakery", "barcode": "8901234567893", "stock": 200, "unit": "kg", "tags": ["flour", "atta", "wheat", "pizza", "bread", "baking"], "seller_id": str(seller1_id), "seller_name": "Mumbai Fresh Mart", "location": {"type": "Point", "coordinates": [MUMBAI_LNG, MUMBAI_LAT]}, "rating": 4.4, "total_sold": 312},
    {"name": "Mozzarella Cheese", "description": "Fresh mozzarella cheese perfect for pizza, pasta, and salads", "price": 249, "category": "Dairy", "barcode": "8901234567894", "stock": 40, "unit": "pack", "tags": ["cheese", "mozzarella", "pizza", "dairy", "italian"], "seller_id": str(seller1_id), "seller_name": "Mumbai Fresh Mart", "location": {"type": "Point", "coordinates": [MUMBAI_LNG, MUMBAI_LAT]}, "rating": 4.7, "total_sold": 187},
    {"name": "Tomato Puree", "description": "Rich tomato puree for pizza sauce, pasta, and curries", "price": 65, "category": "Groceries", "barcode": "8901234567895", "stock": 120, "unit": "can", "tags": ["tomato", "sauce", "pasta", "pizza", "puree"], "seller_id": str(seller2_id), "seller_name": "Quick Grocers", "location": {"type": "Point", "coordinates": [MUMBAI_LNG + 0.01, MUMBAI_LAT + 0.01]}, "rating": 4.3, "total_sold": 234},
    {"name": "Basmati Rice", "description": "Long grain basmati rice for biryani, pulao, and everyday cooking", "price": 180, "category": "Groceries", "barcode": "8901234567896", "stock": 150, "unit": "kg", "tags": ["rice", "basmati", "biryani", "pulao", "grain"], "seller_id": str(seller2_id), "seller_name": "Quick Grocers", "location": {"type": "Point", "coordinates": [MUMBAI_LNG + 0.01, MUMBAI_LAT + 0.01]}, "rating": 4.9, "total_sold": 423},
    {"name": "Chicken (500g)", "description": "Fresh farm chicken cleaned and cut for biryani, curry, and grilling", "price": 199, "category": "Meat", "barcode": "8901234567897", "stock": 25, "unit": "pack", "tags": ["chicken", "biryani", "meat", "protein", "fresh"], "seller_id": str(seller2_id), "seller_name": "Quick Grocers", "location": {"type": "Point", "coordinates": [MUMBAI_LNG + 0.01, MUMBAI_LAT + 0.01]}, "rating": 4.6, "total_sold": 289},
    {"name": "Pasta (Penne)", "description": "Italian penne pasta for pasta dishes, salads, and baked pasta", "price": 85, "category": "Groceries", "barcode": "8901234567898", "stock": 90, "unit": "pack", "tags": ["pasta", "penne", "italian", "noodles", "dinner"], "seller_id": str(seller2_id), "seller_name": "Quick Grocers", "location": {"type": "Point", "coordinates": [MUMBAI_LNG + 0.01, MUMBAI_LAT + 0.01]}, "rating": 4.4, "total_sold": 176},
    {"name": "Cold Pressed Orange Juice", "description": "Fresh squeezed orange juice full of Vitamin C, great for cold and immunity", "price": 149, "category": "Beverages", "barcode": "8901234567899", "stock": 35, "unit": "bottle", "tags": ["juice", "orange", "vitamin c", "immunity", "cold", "fresh"], "seller_id": str(seller1_id), "seller_name": "Mumbai Fresh Mart", "location": {"type": "Point", "coordinates": [MUMBAI_LNG, MUMBAI_LAT]}, "rating": 4.8, "total_sold": 156},
    {"name": "Eggs (12 pack)", "description": "Farm fresh eggs for breakfast, baking, and cooking", "price": 89, "category": "Dairy", "barcode": "8901234567900", "stock": 60, "unit": "dozen", "tags": ["eggs", "breakfast", "protein", "farm fresh", "baking"], "seller_id": str(seller2_id), "seller_name": "Quick Grocers", "location": {"type": "Point", "coordinates": [MUMBAI_LNG + 0.01, MUMBAI_LAT + 0.01]}, "rating": 4.5, "total_sold": 398},
    {"name": "Biryani Masala", "description": "Special blend of spices for authentic Hyderabadi biryani", "price": 75, "category": "Spices", "barcode": "8901234567901", "stock": 70, "unit": "pack", "tags": ["biryani", "masala", "spices", "hyderabadi", "cooking"], "seller_id": str(seller1_id), "seller_name": "Mumbai Fresh Mart", "location": {"type": "Point", "coordinates": [MUMBAI_LNG, MUMBAI_LAT]}, "rating": 4.7, "total_sold": 267},
]

# Add embedding placeholder (will be generated by API on first search)
for p in products:
    p["embedding"] = None
    p["created_at"] = datetime.utcnow()

result = db.products.insert_many(products)
print(f"  ✅ Inserted {len(result.inserted_ids)} products")

# Create 2dsphere index for geo queries
db.products.create_index([("location", "2dsphere")])
print("  ✅ Geo index created")

print("\n🎉 Seed complete! Demo credentials:")
print("   Buyer:    buyer@demo.com   / demo1234")
print("   Seller 1: seller@demo.com  / demo1234")
print("   Seller 2: seller2@demo.com / demo1234")
print("\n   Products loaded: 12 items across 2 shops")
print("   Run the backend to start serving!\n")
