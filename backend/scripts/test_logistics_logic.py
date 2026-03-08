import asyncio
import httpx
import sys
import os

async def test_preview_api():
    url = "http://localhost:8000/orders/preview"
    # Need a valid token. For now, let's just test the logic internally if possible, 
    # but a full API call is better.
    # I'll create a script that just calls the optimizer directly with "Mnit Jaipur"
    print("🚀 Testing Logistics Logic for 'Mnit Jaipur'...")
    
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services.delivery_route_optimizer import DeliveryRouteOptimizer
    from database import get_products_collection, get_users_collection
    
    # Mock items (Exact names from DB)
    items = [
        {"product_name": "Eyeshadow Palette With Mirror", "quantity": 1},
        {"product_name": "Red Lipstick", "quantity": 1}
    ]
    
    products_col = get_products_collection()
    users_col = get_users_collection()
    
    optimizer = DeliveryRouteOptimizer()
    print("🔍 Step 1: Geocoding 'Mnit Jaipur'...")
    success = await optimizer.resolve_buyer_location("Mnit Jaipur")
    print(f"   Coords: {optimizer.buyer_lat, optimizer.buyer_lng} (Success: {success})")
    
    print("🔍 Step 2: Optimizing Shops...")
    shops = await optimizer.optimize_shops(items, products_col, users_col)
    print(f"   Shops found: {len(shops)}")
    for s in shops:
        print(f"   - {s['shop_name']} ({s['lat']}, {s['lng']})")
        
    print("🔍 Step 3: Solving Route...")
    plan = await optimizer.solve_route(shops)
    print(f"✅ Final Distance: {plan['total_distance_km']} km")
    print(f"✅ Route: {plan['optimal_route_summary']}")

if __name__ == "__main__":
    asyncio.run(test_preview_api())
