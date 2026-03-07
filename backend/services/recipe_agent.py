import json
import os
import random
import math
import logging
import re
from dotenv import load_dotenv
from database import get_products_collection
from services.ai.gemini_service import gemini_service
from services.ai.rate_limit_manager import manager

load_dotenv()

# Logger
logger = logging.getLogger("recipe_agent")

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def parse_recipe_ingredients(meal_request: str, model_name: str = None) -> dict:
    """
    Use upgraded GeminiService to extract ingredients.
    V4 UPDATE: Batch Parsing - Can handle multiple requests or heavy single request.
    Returns a dict with 'ingredients' and 'status'.
    """
    system_instruction = (
        "You are a smart grocery assistant. Extract ingredients and approximate quantities needed. "
        "Return ONLY a JSON object with two keys: "
        "'ingredients': list of {ingredient, quantity} objects (max 20), "
        "'warning': null or a string if you had to truncate. "
        "CRITICAL: Keep ingredient names clean (no parentheses, no notes like 'optional'). "
        "Example: {'ingredients': [{'ingredient': 'Mozzarella', 'quantity': '200g'}], 'warning': null}"
    )
    
    prompt = f"User wants to cook: '{meal_request}'. Return realistic ingredients needed to buy."

    try:
        response_text = await gemini_service.generate_content(prompt, system_instruction=system_instruction)
        if not response_text:
            return {"ingredients": [], "warning": "AI service temporarily unavailable due to quota limits.", "status": "failed"}

        # Robust JSON extraction
        clean_json = gemini_service.extract_json(response_text)
        if not clean_json:
            logger.error(f"Failed to extract JSON from AI response: {response_text[:100]}...")
            return {"ingredients": [], "warning": "AI returned unusable data format.", "status": "error"}
        
        data = json.loads(clean_json)
        return {
            "ingredients": data.get("ingredients", []),
            "warning": data.get("warning"),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Recipe parsing failed: {e}")
        return {"ingredients": [], "warning": "Failed to parse recipe details.", "status": "error"}


async def find_ingredients_from_db(ingredients: list, buyer_lat: float = None, buyer_lng: float = None) -> dict:
    """
    Search DB for ingredients. 
    V4 UPDATE: Proactive Quota Check and Partial Result Safety.
    Returns {results: [...], meta: {partial: bool, message: str}}
    """
    products_col = get_products_collection()
    results = []
    is_partial = False
    message = ""

    for i, item in enumerate(ingredients):
        ingredient_name = item.get("ingredient", "")
        quantity = item.get("quantity", "1 unit")
        
        # Sanitize for regex
        safe_name = re.escape(ingredient_name)

        # 1. Search DB first (Always safe)
        cursor = products_col.find({
            "$or": [
                {"name": {"$regex": f"^{safe_name}$", "$options": "i"}}, # Exact first
                {"name": {"$regex": safe_name, "$options": "i"}},
                {"tags": {"$regex": safe_name, "$options": "i"}},
                {"category": {"$regex": safe_name, "$options": "i"}}
            ],
            "stock": {"$gt": 0}
        }).limit(3)

        found = await cursor.to_list(length=3)
        best = None
        best_dist = float("inf")

        for product in found:
            dist = None
            if buyer_lat and buyer_lng and product.get("location"):
                coords = product["location"].get("coordinates", [0, 0])
                dist = haversine_km(buyer_lat, buyer_lng, coords[1], coords[0])
                if dist < best_dist:
                    best_dist = dist
                    best = product
            else:
                if best is None:
                    best = product

        # 2. Mock Generation with Proactive Quota Check
        if best is None:
            # V4 Logic: If we are low on quota (proactive check), we stop generating new products
            # to ensure the UI remains fast and the user sees what IS available.
            
            logger.info(f"Ingredient '{ingredient_name}' missing, checking quota for generation...")
            
            # Check if ANY key has ANY model with available RPD
            can_generate = False
            from services.ai.gemini_service import API_KEYS, MODEL_PRIORITY
            for key in API_KEYS:
                for model in MODEL_PRIORITY:
                    if manager.can_use(key, model):
                        can_generate = True
                        break
                if can_generate: break

            if can_generate:
                best = await generate_mock_product(ingredient_name, buyer_lat, buyer_lng)
            
            if best is None:
                is_partial = True
                message = "Showing partial results due to AI usage limits."
                logger.warning(f"Skipping auto-generation for '{ingredient_name}' - Quota limit.")

        results.append({
            "ingredient": ingredient_name,
            "needed_quantity": quantity,
            "product": {
                "id": str(best.get("id", best.get("_id"))) if best else "",
                "name": best["name"],
                "price": best["price"],
                "stock": best["stock"],
                "seller_id": str(best["seller_id"]),
                "distance_km": round(best.get("distance_km", 0), 2) if best and "distance_km" in best else (round(best_dist, 2) if best_dist != float("inf") else None)
            } if best else None,
            "found": best is not None
        })

    return {
        "results": results,
        "meta": {
            "partial": is_partial,
            "message": message
        }
    }


async def generate_mock_product(query: str, lat: float = None, lng: float = None) -> dict:
    """Generate a realistic mock product using GeminiService with safety checks."""
    
    # 1. Safety Filter (sentences/verbs)
    if len(query.split()) > 5 or len(query) > 50 or any(verb in query.lower() for verb in ["make", "cook", "prepare", "find"]):
        return None

    prompt = f"Create ONE realistic grocery product for search term: '{query}'. Return ONLY JSON format: {{\"name\": \"...\", \"description\": \"...\", \"price\": 2.99, \"category\": \"...\", \"unit\": \"...\", \"tags\": [...]}}"
    
    try:
        response_text = await gemini_service.generate_content(prompt)
        if not response_text:
            return None # Fail silently or use rule-based fallback below

        text = response_text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        data = json.loads(text.strip())
    except:
        # Final Rule-Based Fallback if AI fails completely
        q_lower = query.lower()
        category = "Groceries"
        if any(w in q_lower for w in ["chicken", "meat", "beef"]): category = "Meat"
        elif any(w in q_lower for w in ["onion", "potato", "carrot"]): category = "Vegetables"
        elif any(w in q_lower for w in ["apple", "fruit", "mango"]): category = "Fruits"
        elif any(w in q_lower for w in ["milk", "cheese", "dairy"]): category = "Dairy"

        data = {
            "name": query.title(),
            "description": f"Fresh and high-quality {query} sourced from local vendors.",
            "price": random.choice([29, 49, 99, 149]),
            "category": category,
            "unit": "1 unit",
            "tags": [query.lower(), category.lower(), "fresh"]
        }

    # Common Document Creation
    try:
        from database import get_users_collection, get_products_collection
        from services.semantic_search import embed_text
        from datetime import datetime
        from bson import ObjectId

        users_col = get_users_collection()
        products_col = get_products_collection()

        # Selection of a relevant seller (Jaipur based)
        seller = await users_col.find_one({"role": "seller"})
        seller_id = str(seller["_id"]) if seller else "000000000000000000000000"
        seller_name = seller.get("name", "Local Shop") if seller else "Local Shop"

        product_lat = lat if lat else 26.8500
        product_lng = lng if lng else 75.8200

        doc = {
            "name": data.get("name", query.title()),
            "description": data.get("description", "Auto-generated product"),
            "price": float(data.get("price", 2.99)),
            "category": data.get("category", "General"),
            "barcode": f"GEN-{random.randint(100000, 999999)}",
            "stock": 50,
            "unit": data.get("unit", "1 pc"),
            "image_url": f"https://placehold.co/400x400?text={query.replace(' ', '+')}",
            "tags": data.get("tags", [query]),
            "seller_id": seller_id,
            "seller_name": seller_name,
            "location": {"type": "Point", "coordinates": [product_lng, product_lat]},
            "embedding": embed_text(f"{data.get('name')} {data.get('description')}"),
            "rating": 4.5,
            "total_sold": 0,
            "is_ai_generated": True,
            "created_at": datetime.utcnow()
        }

        res = await products_col.insert_one(doc)
        doc["id"] = str(res.inserted_id)
        doc.pop("_id", None)
        doc.pop("embedding", None)
        return doc
    except Exception as e:
        logger.error(f"Critical error in mock product creation: {e}")
        return None
