import asyncio
import httpx
from bson import ObjectId
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

async def test_review_system():
    base_url = "http://localhost:8000"
    
    # We need a buyer token
    # For this test, we'll assume the server is running and we can use a known user or create one
    print("Testing Review System...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Login or get a token (assuming a test user exists or we can use the first user in DB)
        # For simplicity in this environment, let's just try to hit the public endpoints first
        
        # Get a sample product
        resp = await client.get(f"{base_url}/products")
        products = resp.json()
        if not products:
            print("No products found to test reviews")
            return
        
        product_id = products[0]["id"]
        print(f"Testing with product: {products[0]['name']} ({product_id})")
        
        # 2. Get reviews (should be empty initially or show existing)
        resp = await client.get(f"{base_url}/products/{product_id}/reviews")
        print(f"Initial reviews: {len(resp.json())}")
        
        # 3. Check Bestsellers
        resp = await client.get(f"{base_url}/analytics/bestsellers")
        print(f"Bestsellers count: {len(resp.json())}")
        if resp.json():
             print(f"Top bestseller: {resp.json()[0]['name']} (Score: {resp.json()[0].get('bestseller_score')})")

if __name__ == "__main__":
    asyncio.run(test_review_system())
