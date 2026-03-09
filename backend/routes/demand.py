from fastapi import APIRouter, HTTPException, Depends
from database import get_product_demand_collection, get_products_collection, get_users_collection
from services.dependencies import require_seller
from typing import Optional
from bson import ObjectId

router = APIRouter()

@router.get("/all")
async def get_all_demand(seller=Depends(require_seller)):
    """List pending product demand requests near the seller."""
    demand_col = get_product_demand_collection()
    users_col = get_users_collection()
    
    # 1. Get seller location
    seller_doc = await users_col.find_one({"_id": seller["_id"]})
    if not seller_doc or not seller_doc.get("location"):
        # Fallback to all pending demand if seller has no location set
        cursor = demand_col.find({"status": "pending"}).sort("request_count", -1)
    else:
        # NearSphere query for local demand (15km)
        cursor = demand_col.find({
            "status": "pending",
            "location": {
                "$nearSphere": {
                    "$geometry": seller_doc["location"],
                    "$maxDistance": 15000 # 15km
                }
            }
        })

    results = await cursor.to_list(length=100)
    
    for r in results:
        r["id"] = str(r["_id"])
        r.pop("_id")
        r["buyer_count"] = r.get("request_count", len(r.get("requested_by", [])))
        
    return results

@router.post("/fulfill/{demand_id}")
async def fulfill_demand(demand_id: str, seller=Depends(require_seller)):
    """Mark a demand request as fulfilled."""
    demand_col = get_product_demand_collection()
    res = await demand_col.update_one(
        {"_id": ObjectId(demand_id)},
        {"$set": {"status": "fulfilled"}}
    )
    if res.modified_count == 0:
        raise HTTPException(status_code=404, detail="Demand request not found.")
    return {"message": "Demand marked as fulfilled."}
