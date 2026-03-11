
import asyncio
from services.product_pairing_service import train_product_pairings
from database import get_product_pairings_collection

async def run_manual_training():
    print("🧹 Cleaning old pairings...")
    pairings_col = get_product_pairings_collection()
    await pairings_col.delete_many({})
    
    print("🧠 Running Apriori training on historical orders...")
    # Using 0.1 support (~2.4 orders) for demo data
    result = await train_product_pairings(min_support=0.1, min_threshold=0.1)
    print(f"Result: {result}")
    
    if result.get("rules_count", 0) > 0:
        sample = await pairings_col.find_one({})
        print(f"Sample rule: {sample}")
    else:
        print("❌ No rules generated. Check if there are paid orders with overlapping items.")

if __name__ == "__main__":
    asyncio.run(run_manual_training())
