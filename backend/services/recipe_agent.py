from google import genai
from google.genai import types
import json
import os
from dotenv import load_dotenv
from database import get_products_collection
import math

load_dotenv()

ALLOWED_MODELS = {
    "gemini-2.0-flash": "gemini-2.0-flash",
    "gemini-2.5-flash": "gemini-2.5-flash",
}
DEFAULT_MODEL = "gemini-2.0-flash"

# Single shared client — initialized once at module load
_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def parse_recipe_ingredients(meal_request: str, model_name: str = DEFAULT_MODEL) -> list:
    """Use Gemini to extract ingredients + quantities from a meal description."""
    resolved_model = ALLOWED_MODELS.get(model_name, DEFAULT_MODEL)
    try:
        prompt = f"""You are a smart grocery assistant. A user wants to cook: "{meal_request}"

Extract the ingredients and approximate quantities needed.
Return ONLY valid JSON in this format (no markdown, no explanation):
[
  {{"ingredient": "flour", "quantity": "500g"}},
  {{"ingredient": "cheese", "quantity": "200g"}},
  {{"ingredient": "tomato sauce", "quantity": "250ml"}}
]

Consider realistic serving sizes. Return 3-8 ingredients maximum."""

        response = _client.models.generate_content(
            model=resolved_model,
            contents=prompt,
        )
        text = response.text.strip()
        # Clean up any markdown fences
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        print(f"Gemini error [{resolved_model}]: {e}")
        from fastapi import HTTPException
        if '429' in str(e) or 'quota' in str(e).lower() or 'RESOURCE_EXHAUSTED' in str(e):
            raise HTTPException(status_code=429, detail=f"AI Quota Exceeded for {resolved_model}. Try switching to a different model or wait a moment.")
        # Only fallback for standard parsing errors, not quota blocks
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

        if best is None:
            # Ingredient completely missing from DB? Let the AI imagine it and stock it instantly!
            print(f"Ingredient '{ingredient_name}' missing, auto-generating...")
            best = await generate_mock_product(ingredient_name, buyer_lat, buyer_lng)

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

    return results


async def generate_mock_product(query: str, lat: float = None, lng: float = None) -> dict:
    """Generate a realistic mock product using Gemini when a search turns up empty, saving it to MongoDB instantly."""
    try:
        prompt = f"""A user searched a grocery app for "{query}" but we have no matching products.
Create ONE realistic grocery product that perfectly fulfills this user's search intent.
Make the price realistic.
Return ONLY valid JSON (no markdown fences, no explanation):
{{
    "name": "Product Name",
    "description": "Appealing description of the product.",
    "price": 2.99,
    "category": "Groceries",
    "unit": "1 piece",
    "tags": ["tag1", "tag2"]
}}"""
        response = _client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=prompt,
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        data = json.loads(text.strip())

        from database import get_users_collection, get_products_collection
        from services.semantic_search import embed_text

        users_col = get_users_collection()
        seller = await users_col.find_one({"role": "seller"})
        seller_id = str(seller["_id"]) if seller else "000000000000000000000000"
        seller_name = seller.get("name", "Auto-Generated Shop") if seller else "Auto-Generated Shop"

        # Spawn it near the user so they can order it immediately
        product_lat = lat if lat else 28.6139
        product_lng = lng if lng else 77.2090

        doc = {
            "name": data.get("name", query.title()),
            "description": data.get("description", "Auto-generated product"),
            "price": float(data.get("price", 2.99)),
            "category": data.get("category", "General"),
            "barcode": None,
            "stock": 100,
            "unit": data.get("unit", "1 pc"),
            "image_url": None,
            "tags": data.get("tags", [query]),
            "seller_id": seller_id,
            "seller_name": seller_name,
            "location": {"type": "Point", "coordinates": [product_lng, product_lat]},
            "embedding": embed_text(f"{data.get('name')} {data.get('description')} {data.get('category')} {' '.join(data.get('tags', []))}"),
            "rating": 5.0,
            "total_sold": 0,
            "is_ai_generated": True
        }

        products_col = get_products_collection()
        res = await products_col.insert_one(doc)
        doc["id"] = str(res.inserted_id)
        doc.pop("_id", None)
        doc.pop("embedding", None)

        if lat and lng:
            doc["distance_km"] = 0.0

        return doc
    except Exception as e:
        print(f"Error generating mock product: {e}")
        return None
