import google.generativeai as genai
import json
import os
from dotenv import load_dotenv
from database import get_products_collection
from bson import ObjectId
import math

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

async def parse_recipe_ingredients(meal_request: str) -> list:
    """Use Gemini to extract ingredients + quantities from a meal description."""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
You are a smart grocery assistant. A user wants to cook: "{meal_request}"

Extract the ingredients and approximate quantities needed.
Return ONLY valid JSON in this format (no markdown, no explanation):
[
  {{"ingredient": "flour", "quantity": "500g"}},
  {{"ingredient": "cheese", "quantity": "200g"}},
  {{"ingredient": "tomato sauce", "quantity": "250ml"}}
]

Consider realistic serving sizes. Return 3-8 ingredients maximum.
"""
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Clean up any markdown fences
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        print(f"Gemini error: {e}")
        # Fallback: return basic ingredient list
        return [{"ingredient": meal_request, "quantity": "1 unit"}]

async def find_ingredients_from_db(ingredients: list, buyer_lat: float = None, buyer_lng: float = None) -> list:
    """Search DB for each ingredient, find nearest seller."""
    products_col = get_products_collection()
    results = []

    for item in ingredients:
        ingredient_name = item.get("ingredient", "")
        quantity = item.get("quantity", "1 unit")

        # Search by name similarity
        cursor = products_col.find({
            "$or": [
                {"name": {"$regex": ingredient_name, "$options": "i"}},
                {"tags": {"$regex": ingredient_name, "$options": "i"}},
                {"category": {"$regex": ingredient_name, "$options": "i"}}
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

        results.append({
            "ingredient": ingredient_name,
            "needed_quantity": quantity,
            "product": {
                "id": str(best["_id"]),
                "name": best["name"],
                "price": best["price"],
                "stock": best["stock"],
                "seller_id": str(best["seller_id"]),
                "distance_km": round(best_dist, 2) if best_dist != float("inf") else None
            } if best else None,
            "found": best is not None
        })

    return results
