
import asyncio
import random
from database import get_orders_collection
from motor.motor_asyncio import AsyncIOMotorCollection

# Realistic Jaipur neighborhoods for demand clustering
JAIPUR_NEIGHBORHOODS = [
    {"name": "Malviya Nagar", "lat": 26.8510, "lng": 75.8050},
    {"name": "Vaishali Nagar", "lat": 26.9020, "lng": 75.7450},
    {"name": "Mansarovar", "lat": 26.8620, "lng": 75.7850},
    {"name": "C-Scheme", "lat": 26.9100, "lng": 75.7900},
    {"name": "Raja Park", "lat": 26.9050, "lng": 75.7920},
    {"name": "Jagatpura", "lat": 26.8350, "lng": 75.8650},
    {"name": "Bani Park", "lat": 26.9270, "lng": 75.7900},
    {"name": "Jawahar Nagar", "lat": 26.8950, "lng": 75.8250},
    {"name": "Shastri Nagar", "lat": 26.9400, "lng": 75.7850},
    {"name": "Civil Lines", "lat": 26.9050, "lng": 75.7750}
]

async def fix_data():
    orders_col = get_orders_collection()
    
    # 1. Find orders with [0,0] or missing coordinates
    query = {
        "status": "paid",
        "$or": [
            {"buyer_location.coordinates": [0, 0]},
            {"buyer_location": {"$exists": False}},
            {"buyer_location.coordinates": {"$exists": False}}
        ]
    }
    
    orders = await orders_col.find(query).to_list(length=100)
    print(f"Found {len(orders)} orders with invalid coordinates. Fixing...")
    
    updated_count = 0
    for order in orders:
        # Pick a random neighborhood
        area = random.choice(JAIPUR_NEIGHBORHOODS)
        
        # Add jitter (within ~800m)
        lat_jitter = (random.random() - 0.5) * 0.015
        lng_jitter = (random.random() - 0.5) * 0.015
        
        new_lat = area["lat"] + lat_jitter
        new_lng = area["lng"] + lng_jitter
        
        # Update order
        await orders_col.update_one(
            {"_id": order["_id"]},
            {"$set": {
                "buyer_location": {
                    "type": "Point",
                    "coordinates": [new_lng, new_lat]
                },
                "delivery_address": f"{area['name']}, Jaipur, Rajasthan"
            }}
        )
        updated_count += 1
    
    print(f"Successfully updated {updated_count} orders.")

if __name__ == "__main__":
    asyncio.run(fix_data())
