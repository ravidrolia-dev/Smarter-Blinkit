
import asyncio
import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.geocoding_service import geocoding_service

async def test_specific_geocode():
    queries = ["MNIT Jaipur", "Mnit Jaipur", "Vaishali Nagar Jaipur", "Bani Park Jaipur"]
    for q in queries:
        print(f"🔍 Testing: '{q}'")
        coords = await geocoding_service.get_coordinates(q)
        print(f"   Result: {coords}")
        await asyncio.sleep(1.2) # Nominatim rate limit

if __name__ == "__main__":
    asyncio.run(test_specific_geocode())
