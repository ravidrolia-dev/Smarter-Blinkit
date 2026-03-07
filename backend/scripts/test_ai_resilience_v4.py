import os
import sys
import asyncio
import json

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai.gemini_service import GeminiService
from services.ai.rate_limit_manager import RateLimitManager
from services.recipe_agent import parse_recipe_ingredients, find_ingredients_from_db
from dotenv import load_dotenv

load_dotenv()

async def test_v4_resilience():
    print("\n=== AI Architecture V4 Resilience Test ===")
    
    # 1. Test Batch Parsing
    print("\n[Test 1] Batch Parsing (Pizza)...")
    task = "Make Pizza for 4 people"
    res = await parse_recipe_ingredients(task)
    print(f"Status: {res.get('status')}")
    print(f"Ingredients Found: {len(res.get('ingredients', []))}")
    if res.get("warning"):
        print(f"⚠️ Warning: {res['warning']}")

    # 2. Test Model Fallback & Quota Protection
    print("\n[Test 2] Quota Protection & Partial Results...")
    # We simulate a list of ingredients where some might trigger mock generation
    test_ingredients = [
        {"ingredient": "San Marzano Tomatoes", "quantity": "2 cans"},
        {"ingredient": "Caputo 00 Flour", "quantity": "1kg"},
        {"ingredient": "Fresh Buffalo Mozzarella", "quantity": "500g"}
    ]
    
    # Run DB search with mock generation
    db_res = await find_ingredients_from_db(test_ingredients)
    print(f"Partial Result Triggered: {db_res['meta']['partial']}")
    if db_res['meta']['message']:
        print(f"📢 System Message: {db_res['meta']['message']}")
    
    for r in db_res['results']:
        status = "✅ Found" if r['found'] else "❌ Not Found"
        print(f" - {r['ingredient']}: {status}")

    print("\n[Test 3] Model Priority Verification...")
    from services.ai.gemini_service import MODEL_PRIORITY
    print(f"Primary Model: {MODEL_PRIORITY[0]} (Should be gemini-3.1-flash-lite)")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_v4_resilience())
