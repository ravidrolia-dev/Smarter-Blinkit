import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.ai.rate_limit_manager import manager
from services.ai.gemini_service import gemini_service

load_dotenv()

async def stress_test():
    print("--- AI Resilience Stress Test ---")
    
    # 1. Test basic generation
    print("\n[Test 1] Basic Generation...")
    resp = await gemini_service.generate_content("Say 'Resilience Active'")
    print(f"Response: {resp}")
    
    # 2. Simulate Quota Exhaustion for KEY_1 / Primary Model
    print("\n[Test 2] Simulating Quota Exhaustion for Primary...")
    first_key = list(gemini_service.clients.keys())[0]
    manager.mark_exhausted(first_key, "gemini-2.0-flash")
    
    print("Requesting again (should fallback to next model or key)...")
    resp2 = await gemini_service.generate_content("Say 'Fallback Working'")
    print(f"Response: {resp2}")
    
    # 3. Test Recipe Agent Integration
    print("\n[Test 3] Testing Recipe Agent Mock Product Protection...")
    from services.recipe_agent import generate_mock_product
    # Should skip due to safety filters (sentence query)
    bad_mock = await generate_mock_product("How do I make a cake for 10 people?")
    if bad_mock is None:
        print("✅ Safety Filter Blocked bad mock request.")
    else:
        print("❌ Safety Filter Failed to block.")

if __name__ == "__main__":
    asyncio.run(stress_test())
