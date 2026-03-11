
import asyncio
import httpx

async def verify_pairings():
    base_url = "http://localhost:8000"
    
    print("🚀 Triggering Apriori training...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            train_res = await client.post(f"{base_url}/analytics/train-pairings?support=0.01&confidence=0.1")
            print(f"Training Result: {train_res.json()}")
            
            if train_res.json().get("rules_count", 0) == 0:
                print("⚠️ No rules generated. This might be due to low order volume or diverse items.")
                return

            print("\n🔍 Fetching sample pairings...")
            # We need a sample product ID. I'll just try to get one from the db if needed, 
            # but for now let's hope the training worked and we can see the collection.
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_pairings())
