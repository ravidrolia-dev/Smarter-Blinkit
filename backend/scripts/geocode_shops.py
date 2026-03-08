import asyncio
import sys
import os
from typing import List

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_users_collection
from services.geocoding_service import geocoding_service

async def geocode_shops():
    print("📍 Starting Shop Geocoding...")
    users_col = get_users_collection()
    
    # Find all sellers
    sellers = await users_col.find({"role": "seller"}).to_list(length=100)
    print(f"Found {len(sellers)} sellers.")

    for seller in sellers:
        name = seller.get("name")
        email = seller.get("email")
        
        # Skip if already has location
        if seller.get("location"):
            # print(f"✅ {name} ({email}) already has coordinates.")
            continue

        print(f"🔍 Geocoding {name}...")
        
        # Try different address variants for better results
        # Adding 'Jaipur' as default context
        queries = [
            f"{name}, Jaipur, Rajasthan",
            f"{name}, Jaipur",
            name
        ]
        
        coords = None
        for q in queries:
            coords = await geocoding_service.get_coordinates(q)
            if coords:
                print(f"   Found: {coords}")
                break
            await asyncio.sleep(1.0) # Rate limiting for Nominatim
        
        if coords:
            lat, lng = coords
            await users_col.update_one(
                {"_id": seller["_id"]},
                {"$set": {
                    "location": {
                        "type": "Point",
                        "coordinates": [lng, lat]
                    }
                }}
            )
            print(f"   ✅ Updated {name}.")
        else:
            # Fallback/Default for specific known names if API fails
            defaults = {
                "Vaishali Mart": (26.9124, 75.7873),
                "Bani Park Corner": (26.9248, 75.8012),
                "Pink City Fresh Mart": (26.9150, 75.8200),
                "Malviya Superstore": (26.8550, 75.8240),
                "Mansarovar Fresh": (26.8770, 75.7600),
                "Jagatpura Essentials": (26.8250, 75.8600),
                "Raja Park Provisions": (26.8950, 75.8300)
            }
            if name in defaults:
                lat, lng = defaults[name]
                await users_col.update_one(
                    {"_id": seller["_id"]},
                    {"$set": {
                        "location": {
                            "type": "Point",
                            "coordinates": [lng, lat]
                        }
                    }}
                )
                print(f"   ⚠️ API failed, used default for {name}: {lat}, {lng}")
            else:
                print(f"   ❌ Could not geocode {name}.")

    print("🏁 Geocoding complete.")

if __name__ == "__main__":
    asyncio.run(geocode_shops())
