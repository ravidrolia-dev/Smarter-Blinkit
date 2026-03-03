from fastapi import APIRouter, Query, Depends
from database import get_products_collection
from services.semantic_search import rank_products_by_query, embed_text
from services.dependencies import get_current_user
from bson import ObjectId
import math
from typing import Optional

router = APIRouter()

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

@router.get("")
async def smart_search(
    q: str = Query(..., description="Natural language search query"),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    limit: int = Query(20)
):
    """
    Semantic intent search. Examples:
      - "I have a cold" → suggests Ginger Tea, Honey
      - "make pasta" → suggests pasta, sauce, parmesan
      - "cold drinks" → suggests cola, juice, water
    """
    products_col = get_products_collection()

    # Fetch all in-stock products (can be optimized with vector index in production)
    cursor = products_col.find({"stock": {"$gt": 0}})
    products = await cursor.to_list(length=500)

    for p in products:
        p["id"] = str(p["_id"])

    # Semantic ranking
    ranked = rank_products_by_query(q, products)

    # Attach distance if user location provided
    if lat and lng:
        for p in ranked:
            loc = p.get("location")
            if loc and loc.get("coordinates"):
                coords = loc["coordinates"]
                p["distance_km"] = round(haversine_km(lat, lng, coords[1], coords[0]), 2)
        # Re-sort: balance score + distance
        ranked.sort(key=lambda x: (-(x.get("_score", 0)), x.get("distance_km", 99)))

    # Clean up and return top results
    results = []
    for p in ranked[:limit]:
        p.pop("embedding", None)
        p.pop("_id", None)
        results.append(p)

    return {"query": q, "results": results, "count": len(results)}
