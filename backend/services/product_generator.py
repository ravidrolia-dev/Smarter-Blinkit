from google import genai
import json
import os
import random
from datetime import datetime
from dotenv import load_dotenv
from database import get_users_collection, get_products_collection
from services.semantic_search import embed_text

load_dotenv()

# Single shared client
_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
_GENERATION_MODEL = "gemini-2.0-flash"  # Fast model for bulk product generation

async def generate_search_products(query: str, lat: float = None, lng: float = None) -> list:
    """Generate up to 5 realistic mock products using Gemini when a search turns up empty or low score. Save to MongoDB permanently."""
    try:
        prompt = f"""A user searched a grocery delivery app for "{query}" but we didn't have strong matches.
Create EXACTLY 5 highly relevant, realistic grocery products to fulfill this search intent.
Ensure diverse options (e.g., different brands, organic vs regular, different sizes).
Return ONLY a valid JSON array of objects (no markdown fences, no explanation).
Format:
[
  {{
    "name": "Product Name",
    "description": "Appealing description of the product.",
    "price": 2.99,
    "category": "Groceries",
    "unit": "1 piece",
    "tags": ["tag1", "tag2"]
  }}
]"""
        response = _client.models.generate_content(
            model=_GENERATION_MODEL,
            contents=prompt,
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        data_list = json.loads(text.strip())

        users_col = get_users_collection()
        seller = await users_col.find_one({"role": "seller"})
        seller_id = str(seller["_id"]) if seller else "000000000000000000000000"
        seller_name = seller.get("name", "BlinkIt Smart Market") if seller else "BlinkIt Smart Market"

        product_lat = lat if lat else 28.6139
        product_lng = lng if lng else 77.2090

        products_col = get_products_collection()
        generated_products = []

        if not isinstance(data_list, list):
            data_list = [data_list]

        for data in data_list[:5]:
            name = data.get("name", query.title())
            # Deduplication: Check if exact name exists
            existing = await products_col.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
            if existing:
                continue

            # placeholder image based on name
            img_text = "+".join(name.split()[:3])

            doc = {
                "name": name,
                "description": data.get("description", "Auto-generated product"),
                "price": float(data.get("price", round(random.uniform(1.5, 25.0), 2))),
                "category": data.get("category", "General"),
                "barcode": None,
                "stock": random.randint(10, 200),
                "unit": data.get("unit", "1 pc"),
                "image_url": f"https://placehold.co/400x400?text={img_text}",
                "tags": data.get("tags", [query]),
                "seller_id": seller_id,
                "seller_name": seller_name,
                "location": {"type": "Point", "coordinates": [product_lng, product_lat]},
                "embedding": embed_text(f"{name} {data.get('description', '')} {data.get('category', '')} {' '.join(data.get('tags', []))}"),
                "rating": round(random.uniform(4.0, 5.0), 1),
                "total_sold": random.randint(0, 500),
                "is_ai_generated": True,
                "auto_generated": True,
                "created_at": datetime.utcnow()
            }
            res = await products_col.insert_one(doc)
            doc["id"] = str(res.inserted_id)
            doc.pop("_id", None)
            doc.pop("embedding", None)

            if lat and lng:
                doc["distance_km"] = 0.0

            generated_products.append(doc)

        return generated_products
    except Exception as e:
        if '429' in str(e) or 'quota' in str(e).lower() or 'RESOURCE_EXHAUSTED' in str(e):
            print(f"Gemini API Quota Exceeded during product generation.")
        else:
            print(f"Error generating search products: {e}")
        return []

async def enhance_product_details(raw_data: dict) -> dict:
    """Use Gemini to polish messy OpenFoodFacts data into professional product details."""
    try:
        # Define available categories for the AI to choose from
        CATEGORIES = ["Groceries", "Snacks", "Beverages", "Dairies", "Vegetables", "Fruits", "Meat", "Essentials", "Bakery", "Personal Care"]
        
        prompt = f"""You are an expert copywriter for a premium grocery delivery app (Smarter BlinkIt).
I will provide raw metadata for a product from OpenFoodFacts. 
Your job is to generate a professional, concise, and appealing set of details.

RAW DATA:
Name: {raw_data.get('name')}
Brand: {raw_data.get('brand')}
Raw Category: {raw_data.get('category')}
Raw Tags: {raw_data.get('tags')}

INSTRUCTIONS:
1. "name": A clean, recognizable title (remove excessive weights or jargon).
2. "description": A short (1-2 sentence) professional and appetizing description.
3. "category": Must be EXACTLY one of these: {CATEGORIES}. Select the best match.
4. "tags": A list of 4-6 highly relevant, lowercase search keywords.

Return ONLY a valid JSON object.

Example Format:
{{
  "name": "Coca-Cola Classic (500ml)",
  "description": "The world's favorite sparkling beverage, delivering a refreshing and uplifting taste with every sip.",
  "category": "Beverages",
  "tags": ["soft drink", "soda", "coke", "carbonated", "chilled"]
}}"""
        
        response = _client.models.generate_content(
            model=_GENERATION_MODEL,
            contents=prompt,
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        
        enhanced = json.loads(text.strip())
        return enhanced
    except Exception as e:
        print(f"Error enhancing product details with AI: {e}")
        # Fallback to original data if AI fails
        return {
            "name": raw_data.get("name"),
            "description": raw_data.get("description", "High quality product."),
            "category": raw_data.get("category", "Groceries"),
            "tags": raw_data.get("tags", [])
        }
