from fastapi import APIRouter
from database import get_products_collection, get_orders_collection
from bson import ObjectId
from collections import defaultdict

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
async def recent_orders(limit: int = 20):
    """Recent paid orders for live storeboard."""
    orders_col = get_orders_collection()
    cursor = orders_col.find({"status": "paid"}).sort("_id", -1).limit(limit)
    orders = await cursor.to_list(length=limit)
    for o in orders:
        o["id"] = str(o.pop("_id"))
    return orders

@router.get("/money-map")
async def money_map():
    """Returns location + sales volume data for neighborhood heatmap."""
    products_col = get_products_collection()
    pipeline = [
        {"$match": {"location": {"$ne": None}, "total_sold": {"$gt": 0}}},
        {"$project": {
            "name": 1,
            "category": 1,
            "total_sold": 1,
            "location": 1,
            "seller_name": 1
        }}
    ]
    products = await products_col.aggregate(pipeline).to_list(length=500)
    for p in products:
        p["id"] = str(p.pop("_id"))
    return {"data_points": products}
