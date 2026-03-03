from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from database import get_orders_collection, get_products_collection
from services.dependencies import require_buyer
from services.neo4j_service import record_order_purchase
from bson import ObjectId
import uuid

router = APIRouter()

class CartItemReq(BaseModel):
    product_id: str
    quantity: int

class CreateOrderReq(BaseModel):
    items: List[CartItemReq]
    delivery_address: str
    buyer_lat: Optional[float] = None
    buyer_lng: Optional[float] = None

class DemoPaymentReq(BaseModel):
    order_id: str  # internal MongoDB _id
    card_name: str
    card_last4: str  # last 4 digits (no real card data stored)

def smart_split_cart(items: list) -> Dict[str, list]:
    """Group cart items by seller."""
    groups: Dict[str, list] = {}
    for item in items:
        seller = item.get("seller_name") or item.get("seller_id") or "Unknown Shop"
        groups.setdefault(seller, []).append(item)
    return groups

@router.post("/create")
async def create_order(req: CreateOrderReq, buyer=Depends(require_buyer)):
    """Create a pending order."""
    products_col = get_products_collection()
    orders_col = get_orders_collection()

    order_items = []
    total = 0.0

    for item in req.items:
        product = await products_col.find_one({"_id": ObjectId(item.product_id)})
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if product["stock"] < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product['name']}")

        line_total = product["price"] * item.quantity
        total += line_total
        order_items.append({
            "product_id": item.product_id,
            "product_name": product["name"],
            "quantity": item.quantity,
            "price": product["price"],
            "seller_id": str(product["seller_id"]),
            "seller_name": product.get("seller_name", ""),
            "line_total": line_total,
        })

    shop_groups = smart_split_cart(order_items)

    order_doc = {
        "items": order_items,
        "buyer_id": str(buyer["_id"]),
        "buyer_name": buyer["name"],
        "total_amount": total,
        "delivery_address": req.delivery_address,
        "buyer_location": {"type": "Point", "coordinates": [req.buyer_lng or 0, req.buyer_lat or 0]},
        "status": "pending",
        "payment_id": None,
        "shop_groups": shop_groups,
    }

    result = await orders_col.insert_one(order_doc)
    return {
        "order_id": str(result.inserted_id),
        "total_amount": total,
        "shop_groups": shop_groups,
        "item_count": len(order_items),
    }

@router.post("/pay")
async def demo_pay(req: DemoPaymentReq, buyer=Depends(require_buyer)):
    """
    Demo payment endpoint — no real gateway.
    Generates a fake transaction ID and marks order as PAID.
    """
    orders_col = get_orders_collection()
    products_col = get_products_collection()

    order = await orders_col.find_one({"_id": ObjectId(req.order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order["buyer_id"] != str(buyer["_id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    if order["status"] == "paid":
        raise HTTPException(status_code=400, detail="Order already paid")

    # Generate fake transaction ID
    transaction_id = f"TXN-{uuid.uuid4().hex[:16].upper()}"

    # Mark order as paid
    await orders_col.update_one(
        {"_id": ObjectId(req.order_id)},
        {"$set": {
            "status": "paid",
            "payment_id": transaction_id,
            "payment_method": "demo",
            "card_name": req.card_name,
            "card_last4": req.card_last4,
        }}
    )

    # Deduct stock and increment total_sold
    product_ids = []
    for item in order["items"]:
        await products_col.update_one(
            {"_id": ObjectId(item["product_id"])},
            {"$inc": {"stock": -item["quantity"], "total_sold": item["quantity"]}}
        )
        product_ids.append(item["product_id"])

    # Record BOUGHT_WITH in Neo4j
    try:
        record_order_purchase(product_ids)
    except Exception:
        pass

    return {
        "success": True,
        "transaction_id": transaction_id,
        "order_id": req.order_id,
        "amount": order["total_amount"],
        "message": "Payment successful",
    }

@router.get("/my-orders")
async def my_orders(buyer=Depends(require_buyer)):
    orders_col = get_orders_collection()
    cursor = orders_col.find({"buyer_id": str(buyer["_id"])}).sort("_id", -1).limit(20)
    orders = await cursor.to_list(length=20)
    for o in orders:
        o["id"] = str(o.pop("_id"))
    return orders
