from fastapi import APIRouter, Depends, HTTPException
from database import get_product_reviews_collection, get_products_collection
from services.dependencies import get_current_user
from models.schemas import ProductReviewUpdate, ProductReviewPublic
from bson import ObjectId
from datetime import datetime
from typing import List

router = APIRouter()

@router.put("/{review_id}")
async def update_review(review_id: str, req: ProductReviewUpdate, user=Depends(get_current_user)):
    reviews_col = get_product_reviews_collection()
    products_col = get_products_collection()

    review = await reviews_col.find_one({"_id": ObjectId(review_id)})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    if review["user_id"] != str(user["_id"]):
        raise HTTPException(status_code=403, detail="You can only update your own reviews")

    updates = {k: v for k, v in req.dict().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    updates["updated_at"] = datetime.utcnow()

    # If rating changed, we need to update product stats
    if "rating" in updates and updates["rating"] != review["rating"]:
        product_id = review["product_id"]
        product = await products_col.find_one({"_id": ObjectId(product_id)})
        if product:
            old_rating = review["rating"]
            new_rating = updates["rating"]
            count = product.get("review_count", 0)
            avg = product.get("rating", 0.0)
            
            # new_avg = (avg * count - old_rating + new_rating) / count
            if count > 0:
                updated_avg = ((avg * count) - old_rating + new_rating) / count
                await products_col.update_one(
                    {"_id": ObjectId(product_id)},
                    {"$set": {"rating": round(updated_avg, 1)}}
                )

    await reviews_col.update_one({"_id": ObjectId(review_id)}, {"$set": updates})
    return {"message": "Review updated"}

@router.delete("/{review_id}")
async def delete_review(review_id: str, user=Depends(get_current_user)):
    reviews_col = get_product_reviews_collection()
    products_col = get_products_collection()

    review = await reviews_col.find_one({"_id": ObjectId(review_id)})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Allow author or admin (though role isn't explicitly passed here, let's stick to author for now)
    if review["user_id"] != str(user["_id"]):
         raise HTTPException(status_code=403, detail="You can only delete your own reviews")

    product_id = review["product_id"]
    rating = review["rating"]

    # Update product stats
    product = await products_col.find_one({"_id": ObjectId(product_id)})
    if product:
        count = product.get("review_count", 0)
        avg = product.get("rating", 0.0)
        
        if count > 1:
            # new_avg = (avg * count - rating) / (count - 1)
            updated_avg = ((avg * count) - rating) / (count - 1)
            await products_col.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": {"rating": round(updated_avg, 1), "review_count": count - 1}}
            )
        else:
            await products_col.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": {"rating": 0.0, "review_count": 0}}
            )

    await reviews_col.delete_one({"_id": ObjectId(review_id)})
    return {"message": "Review deleted"}
