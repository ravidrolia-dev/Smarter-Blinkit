import asyncio
import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.geocoding_service import geocoding_service
from services.route_service import route_service
from services.delivery_route_optimizer import DeliveryRouteOptimizer

async def test_geo_routing():
    print("🌍 Testing Real Geographic Routing...")
    
    # 1. Test Geocoding for MNIT Jaipur
    print("\n🔍 Geocoding 'MNIT Jaipur'...")
    mnit_coords = await geocoding_service.get_coordinates("MNIT Jaipur")
    if mnit_coords:
        print(f"   ✅ Found: {mnit_coords}")
    else:
        print("   ❌ Failed to geocode MNIT Jaipur.")
        return

    # 2. Mock Shops (already geocoded in DB, but we use fixed coords for this test)
    # Vaishali Mart: 26.9124, 75.7873
    # Bani Park Corner: 26.9248, 75.8012
    shops = [
        {"shop_id": "s1", "shop_name": "Vaishali Mart", "lat": 26.9124, "lng": 75.7873, "items": ["Eyeshadow"]},
        {"shop_id": "s2", "shop_name": "Bani Park Corner", "lat": 26.9248, "lng": 75.8012, "items": ["Lipstick"]}
    ]

    # 3. Use Optimizer
    optimizer = DeliveryRouteOptimizer(buyer_lat=mnit_coords[0], buyer_lng=mnit_coords[1])
    
    print("\n🚚 Solving route from MNIT -> Vaishali -> Bani Park -> MNIT...")
    plan = await optimizer.solve_route(shops)
    
    print("\n--- Route Summary ---")
    print(f"Total Distance: {plan['total_distance_km']} km")
    print(f"Estimated Time: {plan['estimated_time_minutes']} min")
    print(f"Route: {plan['optimal_route_summary']}")
    
    if plan['total_distance_km'] > 0:
        print("\n✅ Verification SUCCESS: Real-world routing is working!")
    else:
        print("\n❌ Verification FAILED: Distance is still 0.")

if __name__ == "__main__":
    asyncio.run(test_geo_routing())
