from database import get_orders_collection, get_product_pairings_collection, get_products_collection
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def train_product_pairings(min_support=0.01, min_threshold=0.5):
    """
    Analyzes historical paid orders using a lightweight frequency-based counter.
    Replaces heavy pandas/mlxtend (Apriori) for memory optimization.
    Stores association rules (product_id -> paired_product_id) in the database.
    """
    try:
        orders_col = get_orders_collection()
        pairings_col = get_product_pairings_collection()
        
        # 1. Fetch all paid orders
        cursor = orders_col.find({"status": "paid"}, {"items.product_id": 1})
        orders = await cursor.to_list(length=5000)
        
        if not orders:
            logger.info("No paid orders found for pairing analysis.")
            return {"status": "success", "message": "No orders to analyze", "rules_count": 0}
            
        # 2. Count frequencies
        # item_counts: product_id -> count of orders containing it
        # pair_counts: (id1, id2) -> count of orders containing both
        item_counts = {}
        pair_counts = {}
        total_transactions = len(orders)

        for order in orders:
            items = list(set([item["product_id"] for item in order.get("items", [])]))
            if not items: continue
            
            for i in range(len(items)):
                item_i = items[i]
                item_counts[item_i] = item_counts.get(item_i, 0) + 1
                
                for j in range(i + 1, len(items)):
                    item_j = items[j]
                    pair = tuple(sorted((item_i, item_j)))
                    pair_counts[pair] = pair_counts.get(pair, 0) + 1

        # 3. Generate rules
        # Rule: A -> B
        # Support(A,B) = count(A,B) / total_transactions
        # Confidence(A->B) = count(A,B) / count(A)
        # Lift(A,B) = Support(A,B) / (Support(A) * Support(B))
        
        pairings_to_store = []
        for (id1, id2), count in pair_counts.items():
            support = count / total_transactions
            if support >= min_support:
                # Rule 1: id1 -> id2
                conf1 = count / item_counts[id1]
                if conf1 >= min_threshold:
                    lift1 = support / ((item_counts[id1]/total_transactions) * (item_counts[id2]/total_transactions))
                    pairings_to_store.append({
                        "product_id": str(id1),
                        "paired_product_id": str(id2),
                        "confidence": float(conf1),
                        "support": float(support),
                        "lift": float(lift1),
                        "created_at": datetime.utcnow()
                    })
                
                # Rule 2: id2 -> id1
                conf2 = count / item_counts[id2]
                if conf2 >= min_threshold:
                    lift2 = support / ((item_counts[id1]/total_transactions) * (item_counts[id2]/total_transactions))
                    pairings_to_store.append({
                        "product_id": str(id2),
                        "paired_product_id": str(id1),
                        "confidence": float(conf2),
                        "support": float(support),
                        "lift": float(lift2),
                        "created_at": datetime.utcnow()
                    })

        # 4. Save rules to MongoDB
        await pairings_col.delete_many({})
        if pairings_to_store:
            # Sort by confidence descending to keep top ones if list is huge
            pairings_to_store.sort(key=lambda x: x["confidence"], reverse=True)
            await pairings_col.insert_many(pairings_to_store[:5000]) # Cap at 5000 rules
            
        return {
            "status": "success", 
            "message": f"Successfully trained with {len(pairings_to_store)} rules (Memory Optimized)",
            "rules_count": len(pairings_to_store)
        }

    except Exception as e:
        logger.error(f"Error training product pairings: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

async def get_pairings_for_product(product_id: str, limit: int = 4):
    """
    Fetches precomputed pairings for a product, including basic product info.
    """
    pairings_col = get_product_pairings_collection()
    products_col = get_products_collection()
    
    # 1. Fetch relevant rules sorted by confidence
    cursor = pairings_col.find({"product_id": product_id}).sort("confidence", -1).limit(limit)
    rules = await cursor.to_list(length=limit)
    
    if not rules:
        return []
        
    # 2. Fetch full product details for recommendations
    paired_ids = [r["paired_product_id"] for r in rules]
    
    # Filter out invalid IDs or handle list of strings
    valid_ids = []
    for pid in paired_ids:
        try:
            valid_ids.append(ObjectId(pid))
        except:
            continue
            
    if not valid_ids:
        return []
        
    products_cursor = products_col.find({"_id": {"$in": valid_ids}})
    products = await products_cursor.to_list(length=limit)
    
    # 3. Format result
    result = []
    for p in products:
        p_id = str(p["_id"])
        # Find matching rule for this product to attach confidence
        rule = next((r for r in rules if r["paired_product_id"] == p_id), None)
        
        result.append({
            "id": p_id,
            "name": p.get("name"),
            "price": p.get("price"),
            "image_url": p.get("image_url"),
            "category": p.get("category"),
            "confidence": rule["confidence"] if rule else 0
        })
        
    return result

async def get_pairings_for_cart(product_ids: list, limit: int = 6):
    """
    Suggests items that correlate with multiple items in the cart.
    Ranked by combined confidence.
    """
    if not product_ids:
        return []
        
    pairings_col = get_product_pairings_collection()
    products_col = get_products_collection()
    
    # 1. Fetch rules for all products in cart
    cursor = pairings_col.find({"product_id": {"$in": product_ids}})
    rules = await cursor.to_list(length=100)
    
    if not rules:
        return []
        
    # 2. Aggregate confidence scores
    scores = {} # paired_id -> total_confidence
    for r in rules:
        pid = r["paired_product_id"]
        if pid in product_ids: continue # Don't recommend what's already in cart
        
        scores[pid] = scores.get(pid, 0) + r["confidence"]
        
    # 3. Get top recommendations
    top_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]
    top_id_vals = [ObjectId(tid[0]) for tid in top_ids]
    
    if not top_id_vals:
        return []
        
    # 4. Fetch details
    products = await products_col.find({"_id": {"$in": top_id_vals}}).to_list(length=limit)
    
    result = []
    for p in products:
        p_id = str(p["_id"])
        result.append({
            "id": p_id,
            "name": p.get("name"),
            "price": p.get("price"),
            "image_url": p.get("image_url"),
            "category": p.get("category"),
            "confidence_sum": scores.get(p_id, 0)
        })
        
    return sorted(result, key=lambda x: x["confidence_sum"], reverse=True)
