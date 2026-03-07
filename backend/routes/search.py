from fastapi import APIRouter, Query
from database import get_products_collection
from services.semantic_search import rank_products_by_query, embed_text, SIMILARITY_THRESHOLD
from services.product_generator import generate_search_products
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

async def _fetch_and_rank(q: str, lat: Optional[float], lng: Optional[float], limit: int, threshold: float):
    products_col = get_products_collection()
    cursor = products_col.find({"stock": {"$gt": 0}})
    products = await cursor.to_list(length=500)

    for p in products:
        p["id"] = str(p["_id"])

    ranked = rank_products_by_query(q, products, threshold=threshold, limit=limit)

    # Attach distance if user location provided
    if lat and lng:
        for p in ranked:
            loc = p.get("location")
            if loc and loc.get("coordinates"):
                coords = loc["coordinates"]
                p["distance_km"] = round(haversine_km(lat, lng, coords[1], coords[0]), 2)
        ranked.sort(key=lambda x: (-(x.get("_score", 0)), x.get("distance_km", 99)))

    results = []
    for p in ranked[:limit]:
        p["id"] = str(p.pop("_id", p.get("id")))
        p.pop("embedding", None)
        results.append(p)

    return results


@router.get("")
async def smart_search(
    q: str = Query(..., description="Natural language search query"),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    limit: int = Query(20),
):
    """
    Intent-based semantic search. Examples:
      - "I have a cold" → Honey, Ginger Tea, Tulsi, Turmeric
      - "I feel weak" → Energy Drink, Protein, Multivitamin
      - "make pasta" → Pasta, Sauce, Parmesan
    """
    results = await _fetch_and_rank(q, lat, lng, limit, threshold=SIMILARITY_THRESHOLD)

    best_score = results[0]["_score"] if results else 0.0

    if best_score < 0.5:
        generated = await generate_search_products(q, lat, lng)
        for p in generated:
            p.pop("auto_generated", None)
            results.append(p)

    return {"query": q, "results": results, "count": len(results)}


@router.get("/semantic")
async def semantic_search(
    q: str = Query(..., description="Natural language query"),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    limit: int = Query(10),
    threshold: float = Query(SIMILARITY_THRESHOLD, description="Min similarity score (0-1)"),
):
    """
    Explicit semantic search endpoint with configurable threshold.
    Each result includes `_score` (cosine similarity + intent boost) for debugging.
    """
    results = await _fetch_and_rank(q, lat, lng, limit, threshold=threshold)
    return {
        "query": q,
        "threshold": threshold,
        "results": results,
        "count": len(results),
        "scores": [{"name": p.get("name"), "score": p.get("_score")} for p in results],
    }
