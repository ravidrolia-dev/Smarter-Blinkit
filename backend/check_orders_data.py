
from database import get_orders_collection
import asyncio

async def check_orders():
    orders_col = get_orders_collection()
    paid_orders = await orders_col.count_documents({"status": "paid"})
    print(f"Total paid orders: {paid_orders}")
    
    with_loc = await orders_col.count_documents({
        "status": "paid", 
        "buyer_location.coordinates": {"$exists": True}
    })
    print(f"Paid orders with coordinates: {with_loc}")
    
    if with_loc > 0:
        sample = await orders_col.find_one({"status": "paid", "buyer_location.coordinates": {"$exists": True}})
        print(f"Sample coord: {sample['buyer_location']['coordinates']}")

if __name__ == "__main__":
    asyncio.run(check_orders())
