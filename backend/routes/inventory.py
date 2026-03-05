from fastapi import APIRouter, Depends, HTTPException, Query
from database import get_products_collection
from services.dependencies import require_seller, get_current_user
from bson import ObjectId
from pydantic import BaseModel
from typing import Optional, List
from services.scanner_service import decode_barcode

router = APIRouter()

class StockUpdate(BaseModel):
    quantity_delta: int  # positive = add stock, negative = remove stock
    note: Optional[str] = None

class ScanRequest(BaseModel):
    image_base64: str

import requests

@router.post("/scan")
async def scan_barcode(req: ScanRequest, user=Depends(get_current_user)):
    """Process a captured frame and return the decoded barcode + diagnostic metadata."""
    # print(f"--- Professional Scan request received ---")
    result = await decode_barcode(req.image_base64)
    # result is a dict: {"barcode": ..., "low_light": ..., "is_blurry": ...}
    return result

@router.get("/barcode/{barcode}")
async def lookup_by_barcode(barcode: str, user=Depends(get_current_user)):
    """Look up a product using its barcode, with OpenFoodFacts fallback."""
    products_col = get_products_collection()
    
    # 1. Check current user's inventory (if they are a seller)
    product = await products_col.find_one({
        "barcode": barcode,
        "seller_id": str(user["_id"])
    })
    
    if product:
        product["id"] = str(product.pop("_id"))
        product.pop("embedding", None)
        return {"found": True, "owned": True, "product": product}

    # 2. Check global database (other sellers)
    product = await products_col.find_one({"barcode": barcode})
    if product:
        product["id"] = str(product.pop("_id"))
        product.pop("embedding", None)
        return {"found": True, "owned": False, "product": product}

    # 3. OpenFoodFacts Fallback (Professional Auto-Fill)
    try:
        off_url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        response = requests.get(off_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 1:
                off_prod = data.get("product", {})
                return {
                    "found": True, 
                    "owned": False, 
                    "external": True,
                    "product": {
                        "name": off_prod.get("product_name", "Unknown Product"),
                        "brand": off_prod.get("brands", "Unknown Brand"),
                        "category": off_prod.get("categories", "").split(",")[0],
                        "image": off_prod.get("image_url"),
                        "barcode": barcode,
                        "price": 0,
                        "stock": 0,
                        "unit": "unit"
                    }
                }
    except Exception as e:
        print(f"OpenFoodFacts lookup failed: {e}")

    raise HTTPException(status_code=404, detail=f"No product with barcode {barcode}")

@router.patch("/{product_id}/stock")
async def update_stock(product_id: str, req: StockUpdate, seller=Depends(require_seller)):
    """Update stock for a product. Used by barcode scanner after scanning a box."""
    products_col = get_products_collection()

    product = await products_col.find_one({
        "_id": ObjectId(product_id),
        "seller_id": str(seller["_id"])
    })
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not yours")

    new_stock = product["stock"] + req.quantity_delta
    if new_stock < 0:
        raise HTTPException(status_code=400, detail="Stock cannot be negative")

    await products_col.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {"stock": new_stock}}
    )
    return {
        "product_id": product_id,
        "product_name": product["name"],
        "old_stock": product["stock"],
        "delta": req.quantity_delta,
        "new_stock": new_stock
    }

@router.get("/my-products")
async def seller_inventory(seller=Depends(require_seller)):
    """List all products for the current seller with their stock levels."""
    products_col = get_products_collection()
    cursor = products_col.find({"seller_id": str(seller["_id"])}).sort("name", 1)
    products = await cursor.to_list(length=200)
    for p in products:
        p["id"] = str(p.pop("_id"))
        p.pop("embedding", None)
    return products
