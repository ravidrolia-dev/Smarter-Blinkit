from fastapi import APIRouter
from database import get_products_collection, get_orders_collection, get_shops_collection
from bson import ObjectId
from collections import defaultdict

from routes.products import calculate_bestseller_score, format_product
from database import get_product_reviews_collection

router = APIRouter()

@router.get("/top-products")
async def top_products(limit: int = 10):
    """Products selling the fastest right now."""
    products_col = get_products_collection()
    cursor = products_col.find({"total_sold": {"$gt": 0}}).sort("total_sold", -1).limit(limit)
    products = await cursor.to_list(length=limit)
    for p in products:
        p["id"] = str(p.pop("_id"))
        p.pop("embedding", None)
    return products

@router.get("/top-shops")
async def top_shops(limit: int = 10):
    """Top sellers by units sold."""
    products_col = get_products_collection()
    pipeline = [
        {"$match": {"total_sold": {"$gt": 0}}},
        {"$group": {
            "_id": "$seller_id",
            "seller_name": {"$first": "$seller_name"},
            "total_sales": {"$sum": "$total_sold"},
            "total_revenue": {"$sum": {"$multiply": ["$price", "$total_sold"]}},
            "product_count": {"$sum": 1}
        }},
        {"$sort": {"total_sales": -1}},
        {"$limit": limit}
    ]
    result = await products_col.aggregate(pipeline).to_list(length=limit)
    return result

@router.get("/category-breakdown")
async def category_breakdown():
    """Sales by product category — for Money Map."""
    products_col = get_products_collection()
    pipeline = [
        {"$group": {
            "_id": "$category",
            "total_sold": {"$sum": "$total_sold"},
            "product_count": {"$sum": 1},
            "avg_price": {"$avg": "$price"}
        }},
        {"$sort": {"total_sold": -1}}
    ]
    return await products_col.aggregate(pipeline).to_list(length=50)

@router.get("/recent-orders")
async def recent_orders(seller_id: str = None, limit: int = 20):
    """Recent paid orders. If seller_id is provided, only shows orders containing their items."""
    orders_col = get_orders_collection()
    query = {"status": "paid"}
    if seller_id:
        query["items.seller_id"] = seller_id

    cursor = orders_col.find(query).sort("_id", -1).limit(limit)
    orders = await cursor.to_list(length=limit)
    
    for o in orders:
        o["id"] = str(o.pop("_id"))
        if seller_id:
            # Only show items belonging to THIS seller
            o["items"] = [item for item in o["items"] if item.get("seller_id") == seller_id]
            # Recalculate total for THIS seller's view
            o["total_amount"] = sum(item.get("line_total", 0) for item in o["items"])
            
    return orders

from datetime import datetime, timedelta
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Simple cache for analytics
_analytics_cache = {
    "money_map": None,
    "last_updated": None
}

@router.get("/money-map")
async def money_map(days: int = 30, category: str = None, seller_id: str = None):
    """
    Advanced Money Map visualization data.
    Aggregates paid orders by neighborhood/area.
    Detects shop opportunities and per-seller market share.
    """
    global _analytics_cache
    
    try:
        # Check cache (10 min expiry)
        cache_key = f"money_map_{days}_{category}_{seller_id}"
        if (_analytics_cache.get(cache_key) and 
            _analytics_cache["last_updated"] > datetime.utcnow() - timedelta(minutes=10)):
            return _analytics_cache[cache_key]

        orders_col = get_orders_collection()
        shops_col = get_shops_collection()
        
        # 1. Filter orders
        time_limit = datetime.utcnow() - timedelta(days=days)
        query = {"status": "paid", "$or": [
            {"created_at": {"$gte": time_limit}},
            {"created_at": {"$exists": False}}
        ]}
        
        cursor = orders_col.find(query)
        orders = await cursor.to_list(length=2000)
        
        # 2. Aggregate by area
        area_stats = defaultdict(lambda: {
            "total_orders": 0,
            "total_revenue": 0,
            "seller_orders": 0,
            "seller_revenue": 0,
            "product_counts": defaultdict(int),
            "category_counts": defaultdict(int),
            "lats": [],
            "lngs": [],
            "sample_address": ""
        })
        
        for order in orders:
            items = order.get("items", [])
            
            # For seller share calculation
            has_seller_item = False
            seller_order_rev = 0
            if seller_id:
                seller_items = [i for i in items if i.get("seller_id") == seller_id]
                if seller_items:
                    has_seller_item = True
                    seller_order_rev = sum(i.get("line_total", 0) for i in seller_items)

            if category:
                items = [i for i in items if i.get("category") == category]
                if not items: continue

            # Coordinate extraction
            loc_doc = order.get("buyer_location")
            if not isinstance(loc_doc, dict): continue
            coords = loc_doc.get("coordinates")
            if not isinstance(coords, list) or len(coords) < 2: continue
            
            lng, lat = coords[0], coords[1]
            if lat == 0 or lng == 0: continue
            
            area_key = (round(lat, 2), round(lng, 2))
            stats = area_stats[area_key]
            
            stats["total_orders"] += 1
            stats["total_revenue"] += order.get("total_amount", 0)
            
            if has_seller_item:
                stats["seller_orders"] += 1
                stats["seller_revenue"] += seller_order_rev

            stats["lats"].append(lat)
            stats["lngs"].append(lng)
            if not stats["sample_address"]:
                stats["sample_address"] = order.get("delivery_address", "")
                
            for item in items:
                name = item.get("product_name", "Unknown")
                stats["product_counts"][name] += item.get("quantity", 1)
                cat = item.get("category", "General")
                stats["category_counts"][cat] += item.get("quantity", 1)

        # 3. Finalize and detect opportunities
        shops_data = await shops_col.find({}).to_list(length=200)
        external_shops = []
        for s in shops_data:
            sloc = s.get("location", {}).get("coordinates", [0, 0])
            external_shops.append({
                "name": s.get("shop_name", "Shop"),
                "lat": sloc[1],
                "lng": sloc[0],
                "type": "shop"
            })

        final_data = []
        from math import sqrt
        for (plat, plng), stats in area_stats.items():
            if not stats["lats"]: continue
            
            avg_lat = sum(stats["lats"]) / len(stats["lats"])
            avg_lng = sum(stats["lngs"]) / len(stats["lngs"])
            
            area_name = stats["sample_address"].split(",")[0].strip() or "Jaipur Area"
            top_products = sorted(stats["product_counts"].items(), key=lambda x: x[1], reverse=True)[:5]
            top_products = [p[0] for p in top_products]
            
            total_items = sum(stats["category_counts"].values())
            cat_breakdown = {k: round((v/total_items)*100, 1) for k, v in stats["category_counts"].items()} if total_items > 0 else {}
            
            # Density Check
            nearby_shops_count = 0
            for s in shops_data:
                sloc_doc = s.get("location")
                if isinstance(sloc_doc, dict):
                    scoords = sloc_doc.get("coordinates")
                    if isinstance(scoords, list) and len(scoords) >= 2:
                        dist = sqrt((scoords[1] - avg_lat)**2 + (scoords[0] - avg_lng)**2)
                        if dist < 0.015: nearby_shops_count += 1
            
            opportunity = (stats["total_orders"] >= 3 and nearby_shops_count <= 1)
                
            final_data.append({
                "area": area_name,
                "lat": avg_lat,
                "lng": avg_lng,
                "total_orders": stats["total_orders"],
                "total_revenue": round(stats["total_revenue"], 2),
                "seller_orders": stats["seller_orders"],
                "seller_revenue": round(stats["seller_revenue"], 2),
                "market_share": round((stats["seller_revenue"] / stats["total_revenue"] * 100), 1) if stats["total_revenue"] > 0 else 0,
                "top_products": top_products,
                "category_breakdown": cat_breakdown,
                "nearby_shops": nearby_shops_count,
                "is_opportunity": opportunity,
                "demand_level": "High" if stats["total_orders"] >= 5 else "Medium" if stats["total_orders"] >= 2 else "Low"
            })

        result = {"data_points": final_data, "shops": external_shops}
        _analytics_cache[cache_key] = result
        _analytics_cache["last_updated"] = datetime.utcnow()
        return result
    except Exception as e:
        logger.error(f"Error in money_map: {e}", exc_info=True)
        return {"data_points": [], "error": str(e)}

@router.get("/bestsellers")
async def get_bestsellers(limit: int = 10):
    """Calculate and return top bestsellers based on the formula."""
    products_col = get_products_collection()
    # Fetch all products (or a significant subset) and calculate score
    # For a real app, this should be cached or pre-calculated
    cursor = products_col.find({"total_sold": {"$gt": 0}})
    products = await cursor.to_list(length=500)
    
    scored_products = []
    for p in products:
        score = calculate_bestseller_score(p)
        p_formatted = format_product(p)
        p_formatted["bestseller_score"] = round(score, 2)
        scored_products.append(p_formatted)
    
    # Sort by score
    scored_products.sort(key=lambda x: x["bestseller_score"], reverse=True)
    return scored_products[:limit]

@router.get("/seller-reviews")
async def get_seller_reviews(seller_id: str, limit: int = 20):
    """All reviews for products belonging to a specific seller."""
    products_col = get_products_collection()
    reviews_col = get_product_reviews_collection()
    
    # 1. Get all product IDs for this seller
    seller_products = await products_col.find({"seller_id": seller_id}, {"_id": 1, "name": 1, "image_url": 1, "rating": 1, "review_count": 1}).to_list(length=1000)
    product_map = {str(p["_id"]): p for p in seller_products}
    product_ids = list(product_map.keys())
    
    if not product_ids:
        return []
        
    # 2. Get reviews for these products
    cursor = reviews_col.find({"product_id": {"$in": product_ids}}).sort("created_at", -1).limit(limit)
    reviews = await cursor.to_list(length=limit)
    
    for r in reviews:
        r["id"] = str(r.pop("_id"))
        pid = r["product_id"]
        r["product_name"] = product_map.get(pid, {}).get("name", "Unknown Product")
        r["product_image"] = product_map.get(pid, {}).get("image_url")
        
    return reviews

from services.product_pairing_service import get_pairings_for_product, get_pairings_for_cart, train_product_pairings

@router.get("/products/{product_id}/pairings")
async def product_pairings(product_id: str, limit: int = 4):
    """Get frequently bought together products for a specific item."""
    return await get_pairings_for_product(product_id, limit)

@router.get("/cart/pairings")
async def cart_pairings(ids: str, limit: int = 6):
    """Get recommendations based on current cart (comma separated IDs)."""
    product_ids = [pid.strip() for pid in ids.split(",") if pid.strip()]
    return await get_pairings_for_cart(product_ids, limit)

@router.post("/train-pairings")
async def trigger_training(support: float = 0.01, confidence: float = 0.5):
    """Manually trigger the Apriori training process."""
    return await train_product_pairings(min_support=support, min_threshold=confidence)
