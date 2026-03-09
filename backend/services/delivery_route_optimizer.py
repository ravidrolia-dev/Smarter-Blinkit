import math
from typing import List, Dict, Any, Optional, Tuple
from bson import ObjectId
from .geocoding_service import geocoding_service
from .route_service import route_service

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine formula to calculate distance between two points in km."""
    R = 6371.0  # Earth radius in km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

class DeliveryRouteOptimizer:
    def __init__(self, buyer_lat: Optional[float] = None, buyer_lng: Optional[float] = None):
        self.buyer_lat = buyer_lat
        self.buyer_lng = buyer_lng
        self.avg_speed_kmh = 30.0
        self.pickup_buffer_min = 3.0 # Slightly higher for reality

    async def resolve_buyer_location(self, address: str) -> bool:
        """Try to geocode address if coordinates are missing."""
        if self.buyer_lat is not None and self.buyer_lng is not None:
            return True
        
        coords = await geocoding_service.get_coordinates(address)
        if coords:
            self.buyer_lat, self.buyer_lng = coords
            return True
        return False

    async def optimize_shops(self, items: List[Dict[str, Any]], products_col, users_col) -> List[Dict[str, Any]]:
        """
        Logic to reduce number of shops (Optimization #6).
        """
        item_requirements = []
        for item in items:
            name = item.get("product_name")
            p_id = item.get("product_id")
            
            # 1. Try to find the exact product by ID first (most reliable)
            candidates = []
            if p_id:
                try:
                    p = await products_col.find_one({"_id": ObjectId(p_id)})
                    if p and p.get("stock", 0) >= item["quantity"]:
                        candidates = [p]
                except Exception: pass
            
            # 2. If no exact candidate by ID, fallback to name matching (for flexibility)
            if not candidates:
                candidates = await products_col.find({
                    "name": name,
                    "stock": {"$gte": item.get("quantity", 1)}
                }).to_list(length=20)
            
            # Enrich candidates with seller location
            enriched_candidates = []
            for c in candidates:
                seller_id = c.get("seller_id")
                # Handle cases where seller_id might be a string (common in these docs)
                try:
                    s_oid = ObjectId(seller_id) if isinstance(seller_id, str) else seller_id
                    seller = await users_col.find_one({"_id": s_oid})
                except Exception:
                    seller = None
                    
                if seller and "location" in seller:
                    c["lat"] = seller["location"]["coordinates"][1]
                    c["lng"] = seller["location"]["coordinates"][0]
                    c["seller_name"] = seller.get("name", "Unknown Shop")
                    enriched_candidates.append(c)
            item_requirements.append({
                "original_item": item,
                "candidates": enriched_candidates
            })

        # Greedy Set Cover
        uncovered = list(range(len(item_requirements)))
        selected_shops: Dict[str, Dict[str, Any]] = {} # seller_id -> shop_info
        
        while uncovered:
            # Find shop that covers most uncovered items
            best_shop_id = None
            best_coverage = []
            
            # Get unique shops from all candidates of uncovered items
            shop_pool = {}
            for idx in uncovered:
                for cand in item_requirements[idx]["candidates"]:
                    s_id = str(cand["seller_id"])
                    shop_pool.setdefault(s_id, []).append(idx)
            
            # Find best shop
            max_new = -1
            for s_id, indices in shop_pool.items():
                new_indices = [i for i in indices if i in uncovered]
                if len(new_indices) > max_new:
                    max_new = len(new_indices)
                    best_shop_id = s_id
                    best_coverage = new_indices
            
            if not best_shop_id:
                break # Should not happen if data is consistent
            
            # Record the chosen shop and the items it provides
            # Get full cand info from one of the candidates in this shop
            sample_cand = None
            for idx in best_coverage:
                for cand in item_requirements[idx]["candidates"]:
                    if str(cand["seller_id"]) == best_shop_id:
                        sample_cand = cand
                        break
                if sample_cand: break

            selected_shops[best_shop_id] = {
                "shop_id": best_shop_id,
                "shop_name": sample_cand["seller_name"],
                "lat": sample_cand["lat"],
                "lng": sample_cand["lng"],
                "items": []
            }
            
            for idx in best_coverage:
                selected_shops[best_shop_id]["items"].append(item_requirements[idx]["original_item"]["product_name"])
                uncovered.remove(idx)
        
        return list(selected_shops.values())

    async def solve_route(self, shops: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Determine best pickup sequence and calculate REAL metrics.
        """
        # Safety check: if location is missing, we cannot solve a real route.
        if self.buyer_lat is None or self.buyer_lng is None or not shops:
            return {
                "total_distance_km": 0, 
                "estimated_time_minutes": 0, 
                "stops": [],
                "optimal_route_summary": "Your Home"
            }

        # Optimization #7 (Optional): 10km Radius Check
        MAX_RADIUS_KM = 12.0 # Giving some buffer
        for shop in shops:
            dist_to_home = calculate_distance(self.buyer_lat, self.buyer_lng, shop["lat"], shop["lng"])
            if dist_to_home > MAX_RADIUS_KM:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=400, 
                    detail=f"Shop '{shop['shop_name']}' is too far ({round(dist_to_home,1)} km). Delivery is only available within 12km."
                )

        # Step 1: Improved Greedy Nearest Neighbor (working backwards from home)
        # We start from home and find the closest shop, then closest to that shop, etc.
        # Then reverse the list so it ends at home.
        backward_sequence = []
        remaining = list(shops)
        curr_lat, curr_lng = self.buyer_lat, self.buyer_lng
        
        while remaining:
            nearest_idx = -1
            min_d = float('inf')
            for i, shop in enumerate(remaining):
                d = calculate_distance(curr_lat, curr_lng, shop["lat"], shop["lng"])
                if d < min_d:
                    min_d = d
                    nearest_idx = i
            
            shop = remaining.pop(nearest_idx)
            backward_sequence.append(shop)
            curr_lat, curr_lng = shop["lat"], shop["lng"]

        # Reverse to get the forward pickup sequence: Shop1 -> Shop2 -> ... -> Home
        sequence = backward_sequence[::-1]

        # Step 2: Build coordinate list for RouteService [lng, lat]
        coords = []
        for s in sequence:
            coords.append([s["lng"], s["lat"]])
        coords.append([self.buyer_lng, self.buyer_lat])

        # Step 3: Get real metrics and geometry from ORS
        route_result = await route_service.get_optimized_route(coords)

        if route_result:
            total_dist = route_result["total_distance_km"]
            travel_time = route_result["total_duration_minutes"]
            total_time = travel_time + (len(shops) * self.pickup_buffer_min)
            geometry = route_result.get("geometry")
        else:
            # Fallback to Haversine straight-line estimate if ORS API is unavailable
            total_dist = 0.0
            shop_lats = [s["lat"] for s in sequence]
            shop_lngs = [s["lng"] for s in sequence]
            lats = shop_lats + [self.buyer_lat]
            lngs = shop_lngs + [self.buyer_lng]
            for i in range(len(lats) - 1):
                total_dist += calculate_distance(lats[i], lngs[i], lats[i+1], lngs[i+1])

            travel_time = (total_dist / self.avg_speed_kmh) * 60
            total_time = travel_time + (len(shops) * self.pickup_buffer_min)
            geometry = None

        # Step 4: Finalize stop sequence for mapping
        stops = []
        for s in sequence:
            stops.append({
                "type": "shop",
                "name": s["shop_name"],
                "lat": s["lat"],
                "lng": s["lng"],
                "items": s["items"]
            })
        
        # Finally, the buyer's home
        stops.append({
            "type": "buyer",
            "name": "Your Home",
            "lat": self.buyer_lat,
            "lng": self.buyer_lng
        })

        return {
            "total_distance_km": round(total_dist, 2),
            "estimated_time_minutes": round(total_time),
            "stops": stops,
            "geometry": geometry,
            "optimal_route_summary": " -> ".join([s["shop_name"] for s in sequence]) + " -> Your Home"
        }
