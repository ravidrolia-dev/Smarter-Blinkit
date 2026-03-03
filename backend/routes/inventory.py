from fastapi import APIRouter, Depends, HTTPException, Query
from database import get_products_collection
from services.dependencies import require_seller
from bson import ObjectId
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class StockUpdate(BaseModel):
    quantity_delta: int  # positive = add stock, negative = remove stock
    note: Optional[str] = None

@router.get("/barcode/{barcode}")
async def lookup_by_barcode(barcode: str, seller=Depends(require_seller)):
    """Look up a product using its barcode."""
    products_col = get_products_collection()
    product = await products_col.find_one({
        "barcode": barcode,
        "seller_id": str(seller["_id"])
    })

    if not product:
        # Check if any seller has this barcode (suggest to seller)
        product = await products_col.find_one({"barcode": barcode})
        if product:
            product["id"] = str(product.pop("_id"))
            product.pop("embedding", None)
            return {"found": True, "owned": False, "product": product}
        raise HTTPException(status_code=404, detail=f"No product with barcode {barcode}")

    product["id"] = str(product.pop("_id"))
    product.pop("embedding", None)
    return {"found": True, "owned": True, "product": product}

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
