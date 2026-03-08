from fastapi import APIRouter, Depends, HTTPException
import traceback
from pydantic import BaseModel
from typing import List, Optional, Dict
from database import get_orders_collection, get_products_collection, get_users_collection
from services.dependencies import require_buyer
from services.neo4j_service import record_order_purchase
from bson import ObjectId
import uuid
from services.delivery_route_optimizer import DeliveryRouteOptimizer

router = APIRouter()

class CartItemReq(BaseModel):
    product_id: str
    quantity: int

class CreateOrderReq(BaseModel):
    items: List[CartItemReq]
    delivery_address: str
    buyer_lat: Optional[float] = None
    buyer_lng: Optional[float] = None

class EstimateReq(BaseModel):
    items: List[CartItemReq]
    delivery_address: str
    buyer_lat: Optional[float] = None
    buyer_lng: Optional[float] = None

@router.post("/estimate")
async def estimate_delivery(req: EstimateReq):
    """Calculate delivery distance, time and optimized route."""
    try:
        products_col = get_products_collection()
        users_col = get_users_collection()

        optimizer = DeliveryRouteOptimizer(req.buyer_lat, req.buyer_lng)
        
        # 1. Resolve address if coordinates missing
        if not req.buyer_lat or not req.buyer_lng:
            success = await optimizer.resolve_buyer_location(req.delivery_address)
            if not success:
                raise HTTPException(status_code=400, detail="Could not resolve delivery address")

        # 2. Map items to real products with locations
        cart_items = [item.dict() for item in req.items]
        # We need product names for the optimizer's greedy matching
        for item in cart_items:
            p = await products_col.find_one({"_id": ObjectId(item["product_id"])})
            if p:
                item["product_name"] = p["name"]

        # 3. Step 1: Optimize Shops (Reduction)
        shops = await optimizer.optimize_shops(cart_items, products_col, users_col)
        
        # 4. Step 2: Solve Route
        plan = await optimizer.solve_route(shops)
        
        return plan
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERROR in estimate_delivery: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to calculate delivery estimate")

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
    try:
        products_col = get_products_collection()
        orders_col = get_orders_collection()
        users_col = get_users_collection()

        # Fetch full buyer details since the stateless dependency only provides ID and Role
        full_buyer_doc = await users_col.find_one({"_id": buyer["_id"]})
        buyer_name = full_buyer_doc.get("name", "Unknown Buyer") if full_buyer_doc else "Unknown Buyer"

        order_items = []
        total = 0.0

        print(f"DEBUG: Creating order for buyer {buyer['_id']} ({buyer_name}) with {len(req.items)} items")
        for item in req.items:
            try:
                p_id = ObjectId(item.product_id)
            except Exception:
                raise HTTPException(status_code=400, detail=f"Invalid product ID: {item.product_id}")

            product = await products_col.find_one({"_id": p_id})
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
                "seller_name": product.get("seller_name", "Unknown Seller"),
                "line_total": line_total,
            })

        # Group by seller and SANITIZE KEYS (MongoDB keys cannot contain dots)
        raw_groups = smart_split_cart(order_items)
        shop_groups = {k.replace(".", "_"): v for k, v in raw_groups.items()}

        order_doc = {
            "items": order_items,
            "buyer_id": str(buyer["_id"]),
            "buyer_name": buyer_name,
            "total_amount": total,
            "delivery_address": req.delivery_address,
            "buyer_location": {"type": "Point", "coordinates": [req.buyer_lng or 0.0, req.buyer_lat or 0.0]},
            "status": "pending",
            "payment_id": None,
            "shop_groups": shop_groups,
        }

        result = await orders_col.insert_one(order_doc)
        print(f"DEBUG: Order created successfully: {result.inserted_id}")
        return {
            "order_id": str(result.inserted_id),
            "total_amount": total,
            "shop_groups": shop_groups,
            "item_count": len(order_items),
        }
    except HTTPException:
        raise
    except Exception:
        print("❌ ERROR in create_order:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error in create_order")

@router.post("/pay")
async def demo_pay(req: DemoPaymentReq, buyer=Depends(require_buyer)):
    """
    Demo payment endpoint — no real gateway.
    Generates a fake transaction ID and marks order as PAID.
    """
    orders_col = get_orders_collection()
    products_col = get_products_collection()

    print(f"DEBUG: Processing payment for order {req.order_id}")
    order = await orders_col.find_one({"_id": ObjectId(req.order_id)})
    if not order:
        print(f"DEBUG: Order {req.order_id} not found")
        raise HTTPException(status_code=404, detail="Order not found")
    if order["buyer_id"] != str(buyer["_id"]):
        print(f"DEBUG: Order {req.order_id} buyer mismatch")
        raise HTTPException(status_code=403, detail="Access denied")
    if order["status"] == "paid":
        print(f"DEBUG: Order {req.order_id} already paid")
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
