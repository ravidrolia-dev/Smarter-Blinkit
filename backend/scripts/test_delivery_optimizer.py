import sys
import os
import asyncio
import json

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.delivery_route_optimizer import DeliveryRouteOptimizer, calculate_distance

async def test_optimizer():
    print("🚀 Testing Delivery Route Optimizer...")
    
    # User in Jaipur (Malviya Nagar)
    user_lat, user_lng = 26.8549, 75.8243
    
    optimizer = DeliveryRouteOptimizer(user_lat, user_lng)
    
    # Mock Shops
    shops = [
        {"shop_id": "shop_a", "shop_name": "Fresh Mart", "lat": 26.8600, "lng": 75.8300, "items": ["Pasta"]},
        {"shop_id": "shop_b", "shop_name": "Organic Hub", "lat": 26.8700, "lng": 75.8100, "items": ["Milk"]},
        {"shop_id": "shop_c", "shop_name": "City Grocery", "lat": 26.8500, "lng": 75.8000, "items": ["Cheese", "Tomato"]}
    ]
    
    # Test Distance
    d = calculate_distance(user_lat, user_lng, 26.8600, 75.8300)
    print(f"DEBUG: Distance to Shop A: {round(d, 2)} km")
    
    # Test Route Solving
    plan = await optimizer.solve_route(shops)
    
    print("\n--- Delivery Plan ---")
    print(f"Total Distance: {plan['total_distance_km']} km")
    print(f"Est. Time: {plan['estimated_time_minutes']} minutes")
    print(f"Optimal Sequence: {plan['optimal_route_summary']}")
    
    for i, shop in enumerate(plan['shops_sequence']):
        print(f"{i+1}. {shop['shop_name']} ({shop['distance_from_user_km']} km from home) - Items: {shop['items']}")

if __name__ == "__main__":
    asyncio.run(test_optimizer())
