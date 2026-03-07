import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.ai.rate_limit_manager import manager
from services.ai.gemini_service import gemini_service

load_dotenv()

async def test_hardened_ai():
    print("--- Hardened AI Verification ---")
    
    # 1. Test Parallel Racing
    print("\n[Test 1] Parallel Racing...")
    print("Launching requests (Check logs for 'Racing' and 'Winner')...")
    # This should trigger parallel requests for all allowed combinations
    resp = await gemini_service.generate_content("Say 'Racing Successful' in one word.")
    print(f"Final Response: {resp}")
    
    # 2. Test Thread Safety (Simultaneous calls)
    print("\n[Test 2] Thread Safety (Concurrent hits)...")
    tasks = [
        gemini_service.generate_content(f"Quick check {i}") 
        for i in range(5)
    ]
    results = await asyncio.gather(*tasks)
    print(f"Got {len([r for r in results if r])} successful responses concurrently.")
    
    # 3. Verify Calendar Day Reset Logic (Mock check)
    print("\n[Test 3] Calendar Day Reset Logic...")
    from datetime import datetime, timedelta
    first_key = list(gemini_service.clients.keys())[0]
    first_model = "gemini-2.0-flash"
    
    with manager.lock:
        data = manager.usage[first_key][first_model]
        # Force it to yesterday
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        data["last_day_str"] = yesterday
        data["rpd_count"] = 100
        print(f"Manually set count to 100 for yesterday ({yesterday})")
        
        # Trigger reset via _get_usage_data internally
        refreshed = manager._get_usage_data(first_key, first_model)
        if refreshed["rpd_count"] == 0:
            print("✅ Date-based reset successful! Count is now 0.")
        else:
            print(f"❌ Reset failed. Count is {refreshed['rpd_count']}")

if __name__ == "__main__":
    asyncio.run(test_hardened_ai())
