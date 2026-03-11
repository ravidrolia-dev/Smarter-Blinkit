
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from database import get_orders_collection, get_product_pairings_collection, get_products_collection
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def train_product_pairings(min_support=0.01, min_threshold=0.5):
    """
    Analyzes historical paid orders using Market Basket Analysis (Apriori).
    Stores association rules in the database.
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
            
        # 2. Prepare transaction data
        transactions = []
        for order in orders:
            item_ids = [item["product_id"] for item in order.get("items", [])]
            if item_ids:
                transactions.append(item_ids)
                
        if not transactions:
            return {"status": "success", "message": "No transactions found", "rules_count": 0}

        # 3. One-hot encode using TransactionEncoder
        from mlxtend.preprocessing import TransactionEncoder
        
        logger.info(f"Encoding {len(transactions)} transactions...")
        print(f"Encoding {len(transactions)} transactions...")
        
        te = TransactionEncoder()
        te_ary = te.fit(transactions).transform(transactions)
        df = pd.DataFrame(te_ary, columns=te.columns_)
        
        logger.info(f"Encoded shape: {df.shape}")
        print(f"Encoded shape: {df.shape}")

        # 4. Run Apriori
        logger.info("Running apriori...")
        print("Running apriori...")
        # For small datasets with many items, increase support to avoid memory explosion
        frequent_itemsets = apriori(df, min_support=min_support, use_colnames=True, max_len=2)
        
        if frequent_itemsets.empty:
            logger.info(f"No frequent itemsets found with min_support={min_support}")
            print(f"No frequent itemsets found with min_support={min_support}")
            return {"status": "success", "message": "No patterns found", "rules_count": 0}
            
        # 5. Generate association rules
        logger.info("Generating association rules...")
        print("Generating association rules...")
        rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_threshold)
        
        if rules.empty:
            logger.info("No association rules found with min_threshold=" + str(min_threshold))
            return {"status": "success", "message": "No strong rules found", "rules_count": 0}

        # 6. Save rules to MongoDB
        # Clear old pairings
        await pairings_col.delete_many({})
        
        pairings_to_store = []
        for _, row in rules.iterrows():
            # row['antecedents'] and row['consequents'] are frozensets
            for antecedent in row['antecedents']:
                for consequent in row['consequents']:
                    pairings_to_store.append({
                        "product_id": str(antecedent),
                        "paired_product_id": str(consequent),
                        "confidence": float(row['confidence']),
                        "support": float(row['support']),
                        "lift": float(row['lift']),
                        "created_at": datetime.utcnow()
                    })
                    
        if pairings_to_store:
            await pairings_col.insert_many(pairings_to_store)
            
        return {
            "status": "success", 
            "message": f"Successfully trained with {len(pairings_to_store)} rules",
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
