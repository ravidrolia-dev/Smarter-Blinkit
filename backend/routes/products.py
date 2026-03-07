from fastapi import APIRouter, Depends, HTTPException, Query
import os
from database import get_products_collection, get_users_collection
from services.dependencies import get_current_user, require_seller
from services.semantic_search import embed_text
from services.neo4j_service import create_product_node, create_similar_to, sync_similar_products
from bson import ObjectId
from pydantic import BaseModel
from typing import Optional, List
import math

router = APIRouter()

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    mrp: Optional[float] = None
    category: str
    barcode: Optional[str] = None
    stock: int = 0
    unit: str = "piece"
    image_url: Optional[str] = None
    tags: List[str] = []
    lat: Optional[float] = None
    lng: Optional[float] = None
    address: Optional[str] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    description: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    unit: Optional[str] = None
    barcode: Optional[str] = None

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def format_product(p, buyer_lat=None, buyer_lng=None):
    p["id"] = str(p.pop("_id"))
    p.pop("embedding", None)
    if buyer_lat and buyer_lng and p.get("location"):
        coords = p["location"]["coordinates"]
        p["distance_km"] = round(haversine_km(buyer_lat, buyer_lng, coords[1], coords[0]), 2)
    return p

@router.post("", status_code=201)
async def create_product(req: ProductCreate, seller=Depends(require_seller)):
    users_col = get_users_collection()
    user_doc = await users_col.find_one({"_id": seller["_id"]})
    seller_name = user_doc.get("name", "Unknown Seller") if user_doc else "Unknown Seller"

    products_col = get_products_collection()

    # Generate semantic embedding
    text_to_embed = f"{req.name} {req.description} {req.category} {' '.join(req.tags)}"
    embedding = embed_text(text_to_embed)

    location = None
    if req.lat and req.lng:
        location = {"type": "Point", "coordinates": [req.lng, req.lat]}

    doc = {
        "name": req.name,
        "description": req.description,
        "price": req.price,
        "mrp": getattr(req, "mrp", None),
        "category": req.category,
        "barcode": req.barcode,
        "stock": req.stock,
        "unit": req.unit,
        "image_url": req.image_url,
        "tags": req.tags,
        "seller_id": str(seller["_id"]),
        "seller_name": seller_name,
        "location": location,
        "address": getattr(req, "address", None),
        "embedding": embedding,
        "rating": 0.0,
        "total_sold": 0,
    }

    result = await products_col.insert_one(doc)
    product_id = str(result.inserted_id)

    # Register in Neo4j for graph recommendations
    try:
        create_product_node(product_id, req.name, req.category, req.tags)
        # Background sync for similar products
        import asyncio
        asyncio.create_task(sync_similar_products(product_id, req.name, req.category, embedding))
    except Exception:
        pass

    doc["id"] = product_id
    doc.pop("_id", None)
    doc.pop("embedding", None)
    return doc

@router.get("")
async def list_products(
    category: Optional[str] = None,
    seller_id: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    limit: int = 30
):
    products_col = get_products_collection()
    query = {}
    if category:
        query["category"] = {"$regex": category, "$options": "i"}
    if seller_id:
        query["seller_id"] = seller_id

    cursor = products_col.find(query).limit(limit)
    products = await cursor.to_list(length=limit)
    return [format_product(p, lat, lng) for p in products]

@router.get("/{product_id}")
async def get_product(product_id: str, lat: Optional[float] = None, lng: Optional[float] = None):
    products_col = get_products_collection()
    p = await products_col.find_one({"_id": ObjectId(product_id)})
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return format_product(p, lat, lng)

@router.patch("/{product_id}")
async def update_product(product_id: str, req: ProductUpdate, seller=Depends(require_seller)):
    products_col = get_products_collection()
    updates = {k: v for k, v in req.dict().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    result = await products_col.update_one(
        {"_id": ObjectId(product_id), "seller_id": str(seller["_id"])},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found or not yours")
    return {"message": "Product updated"}

@router.get("/{product_id}/recommendations")
async def get_recommendations_endpoint(product_id: str):
    """Graph-based recommendations using Neo4j BOUGHT_WITH + SIMILAR_TO."""
    from services.neo4j_service import get_recommendations
    
    products_col = get_products_collection()
    product = await products_col.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    graph_recs = get_recommendations(product_id)
    
    # Enrich with MongoDB data
    all_ids = [ObjectId(rid) for rid in (graph_recs["similar"] + graph_recs["bought_with"])]
    enriched_products = {}
    if all_ids:
        cursor = products_col.find({"_id": {"$in": all_ids}})
        async for p in cursor:
            pid = str(p["_id"])
            enriched_products[pid] = format_product(p)

    # Separate and format
    similar = [enriched_products[rid] for rid in graph_recs["similar"] if rid in enriched_products]
    bought_with = [enriched_products[rid] for rid in graph_recs["bought_with"] if rid in enriched_products]

    # Rule: If stock == 0, prioritize similar products (already the primary goal)
    # We will ensure the frontend handles the visual prioritization
    
    if not similar and not bought_with:
        # Fallback: same category products
        cursor = products_col.find({
            "category": product.get("category"),
            "_id": {"$ne": ObjectId(product_id)}
        }).limit(8)
        fallback = await cursor.to_list(length=8)
        return {
            "source": "category_fallback", 
            "similar": [format_product(p) for p in fallback],
            "bought_with": []
        }

    return {
        "source": "neo4j_graph",
        "similar": similar,
        "bought_with": bought_with,
        "is_out_of_stock": product.get("stock", 0) <= 0
    }

@router.delete("/{product_id}")
async def delete_product(product_id: str, seller=Depends(require_seller)):
    products_col = get_products_collection()
    result = await products_col.delete_one(
        {"_id": ObjectId(product_id), "seller_id": str(seller["_id"])}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found or not yours")
    return {"message": "Product deleted"}
