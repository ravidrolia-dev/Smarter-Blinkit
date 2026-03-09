import json
import os
import random
import math
import logging
import re
from dotenv import load_dotenv
from database import get_products_collection, get_product_demand_collection, get_recipe_cache_collection
from services.ai.gemini_service import gemini_service
from services.ai.rate_limit_manager import manager
from datetime import datetime

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


async def parse_recipe_ingredients(meal_request: str) -> dict:
    """
    Use Gemini to extract structured recipe data.
    """
    # 1. Check Cache
    cache_col = get_recipe_cache_collection()
    cached = await cache_col.find_one({"meal_query": meal_request.lower().strip()})
    if cached:
        logger.info(f"Recipe cache hit: {meal_request}")
        return cached["data"]

    system_instruction = (
        "You are a master chef and grocery assistant. "
        "Your goal is to extract ONLY raw grocery ingredient names from the dish. "
        "Rules: "
        "- Return ONLY base ingredient names (e.g., 'tomato', 'onion', 'garlic'). "
        "- Remove quantities, measurements, and units (no '1kg', no '2 cloves', no 'tsp'). "
        "- Remove preparation words (no 'chopped', no 'boiled', no 'fresh'). "
        "- Return ingredients exactly as they appear in a grocery store as a singular product. "
        "Return ONLY a JSON object with: "
        "'recipe_name': string, "
        "'ingredients': list of strings (raw product names), "
        "'instructions': list of strings. "
        "Example: {'recipe_name': 'Pasta', 'ingredients': ['penne pasta', 'tomato', 'basil', 'olive oil'], 'instructions': ['Boil water']}"
    )
    
    prompt = f"How to cook: '{meal_request}'? Provide a simple recipe with ingredients list."
    logger.info(f"Recipe request received: {meal_request}")

    try:
        response_text = await gemini_service.generate_content(prompt, system_instruction=system_instruction)
        if not response_text:
            return None

        clean_json = gemini_service.extract_json(response_text)
        if not clean_json: return None
        
        data = json.loads(clean_json)
        
        # Save to Cache
        await cache_col.update_one(
            {"meal_query": meal_request.lower().strip()},
            {"$set": {"data": data, "created_at": datetime.utcnow()}},
            upsert=True
        )
        
        return data
    except Exception as e:
        logger.error(f"Recipe parsing failed: {e}")
        return None


def normalize_ingredient(text: str) -> str:
    """
    Cleans up ingredient strings into raw grocery product names.
    - Lowercase
    - Remove prep words (chopped, sliced, etc.)
    - Remove common units (tbsp, tsp, cup, etc.)
    - Convert plural to singular
    """
    if not text: return ""
    
    # 1. Lowercase and basic cleanup
    text = text.lower().strip()
    
    # 2. Remove common units and preparation styles (including those with numbers)
    # Examples: 500g, 1kg, 2cups, 1tbsp, 1 tablespoon
    unit_pattern = r'\d+\s*(?:g|kg|ml|l|oz|lb|cups|cup|tbsp|tsp|tablespoon|teaspoon|tablespoons|teaspoons|cloves|pieces|piece|grams|gram)\b'
    text = re.sub(unit_pattern, '', text)
    
    # Also remove unit words without numbers just in case
    standalone_units = ["tablespoon", "teaspoon", "cup", "grams", "gram", "cloves", "clove", "pieces", "piece", "packet", "pack", "kg", "grams"]
    for u in standalone_units:
        text = re.sub(rf'\b{u}\b', '', text)
    # words that don't belong in a product name
    remove_words = [
        "chopped", "sliced", "finely", "fresh", "boiled", "mashed", "crushed", 
        "ground", "powdered", "pieces", "diced", "peeled", "minced", "shredded",
        "and", "with", "or", "of", "about", "approx", "approximately", "optional",
        "needed", "to", "taste", "as", "per", "requirement"
    ]
    
    # regex to remove words as standalone words
    for word in remove_words:
        text = re.sub(rf'\b{word}\b', '', text)
        
    # 3. Strip remaining numbers and special chars (like commas, dots)
    text = re.sub(r'[\d\.,/]+', '', text)
    
    # 4. Clean extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 5. Plural to Singular (basic rule-based)
    singular_map = {
        "tomatoes": "tomato",
        "potatoes": "potato",
        "onions": "onion",
        "eggs": "egg",
        "carrots": "carrot",
        "lemons": "lemon",
        "chillies": "chilli",
        "chilies": "chili",
        "peppers": "pepper",
        "mushrooms": "mushroom",
        "cloves": "clove",
        "leaves": "leaf"
    }
    
    # Check whole word mapping first
    if text in singular_map:
        return singular_map[text]
        
    # Handle composite names like "coriander leaves"
    for plural, singular in singular_map.items():
        text = re.sub(rf'\b{plural}\b', singular, text)
            
    if text.endswith("s") and len(text) > 3:
        # Simple suffix check for other common plurals
        if not text.endswith("ss") and not any(text.endswith(x) for x in ["sh", "ch"]): 
            # Very basic check, but safer than unconditional truncation
            text = text[:-1]
            
    return text.strip()


async def find_ingredients_from_db(ingredients: list, user_id: str = None, lat: float = None, lng: float = None) -> list:
    """
    Search DB for ingredients and record demand if missing.
    """
    products_col = get_products_collection()
    demand_col = get_product_demand_collection()
    results = []

    for item in ingredients:
        # item can now be a string from Gemini if we updated the prompt correctly, or old dict
        raw_name = item.get("ingredient", str(item)) if isinstance(item, dict) else str(item)
        ingredient_name = normalize_ingredient(raw_name)
        
        if not ingredient_name: continue
        
        safe_name = re.escape(ingredient_name)

        # 1. Search DB
        cursor = products_col.find({
            "$or": [
                {"name": {"$regex": f"^{safe_name}$", "$options": "i"}},
                {"name": {"$regex": safe_name, "$options": "i"}},
                {"tags": {"$regex": safe_name, "$options": "i"}}
            ],
            "stock": {"$gt": 0}
        }).limit(5)

        found = await cursor.to_list(length=5)
        
        best = None
        best_dist = float("inf")

        for product in found:
            dist = 999
            if lat and lng and product.get("location"):
                coords = product["location"].get("coordinates", [0, 0])
                dist = haversine_km(lat, lng, coords[1], coords[0])
                
            if dist < best_dist:
                best_dist = dist
                best = product

        # 2. Record Demand if not found
        if not best:
            logger.info(f"Ingredient missing: {ingredient_name}. Recording demand.")
            
            # Aggregate: Find existing demand within 5km for this product
            existing_demand = None
            if lat and lng:
                existing_demand = await demand_col.find_one({
                    "product_name": ingredient_name.lower().strip(),
                    "status": "pending",
                    "location": {
                        "$nearSphere": {
                            "$geometry": {"type": "Point", "coordinates": [lng, lat]},
                            "$maxDistance": 5000 # 5km aggregation radius
                        }
                    }
                })

            if existing_demand:
                # Update existing
                await demand_col.update_one(
                    {"_id": existing_demand["_id"]},
                    {
                        "$inc": {"request_count": 1},
                        "$set": {"last_requested": datetime.utcnow()},
                        "$addToSet": {"requested_by": user_id} if user_id else {"$each": []}
                    }
                )
            else:
                # Create new
                await demand_col.insert_one({
                    "product_name": ingredient_name.lower().strip(),
                    "status": "pending",
                    "request_count": 1,
                    "last_requested": datetime.utcnow(),
                    "requested_by": [user_id] if user_id else [],
                    "location": {"type": "Point", "coordinates": [lng or 0, lat or 0]}
                })

        results.append({
            "ingredient": ingredient_name,
            "quantity": "" if raw_name == ingredient_name else raw_name,
            "found": best is not None,
            "product": {
                "id": str(best["_id"]),
                "name": best["name"],
                "price": best["price"],
                "seller_name": best.get("seller_name", "Shop"),
                "distance_km": round(best_dist, 2) if best_dist != float("inf") else None
            } if best else None
        })

    return results
