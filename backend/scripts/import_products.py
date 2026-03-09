import asyncio
import os
import sys
import json
import random
import requests
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv
from google import genai

# Add backend directory to sys.path so we can import from database and services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_users_collection, get_products_collection, get_shops_collection
from services.jwt_utils import get_password_hash
from services.semantic_search import embed_text

load_dotenv()

FALLBACK_IMAGE = "https://images.unsplash.com/photo-1542838132-92c53300491e?q=80&w=1000&auto=format&fit=crop"

# Shared Gemini client
_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
_GENERATION_MODEL = "gemini-3.1-flash-lite"

CATEGORIES = ["Groceries", "Snacks", "Beverages", "Dairy", "Personal Care", "Household", "Health & Wellness", "Electronics", "Stationery", "Baby Products", "Bakery & Cakes", "Fruits & Vegetables", "Meats & Seafood"]

JAIPUR_SELLERS = [
    {
        "name": "Vaishali Mart",
        "email": "vaishali.mart@example.com",
        "address": "Vaishali Nagar, Jaipur",
        "lat": 26.9080, "lng": 75.7480
    },
    {
        "name": "Malviya Superstore",
        "email": "malviya.super@example.com",
        "address": "Malviya Nagar, Jaipur",
        "lat": 26.8528, "lng": 75.8040
    },
    {
        "name": "Mansarovar Fresh",
        "email": "mansarovar.fresh@example.com",
        "address": "Mansarovar, Jaipur",
        "lat": 26.8647, "lng": 75.7592
    },
    {
        "name": "Jagatpura Essentials",
        "email": "jagatpura.essentials@example.com",
        "address": "Jagatpura, Jaipur",
        "lat": 26.8176, "lng": 75.8340
    },
    {
        "name": "Raja Park Provisions",
        "email": "rajapark.provisions@example.com",
        "address": "Raja Park, Jaipur",
        "lat": 26.8946, "lng": 75.8354
    },
    {
        "name": "Bani Park Corner",
        "email": "banipark.corner@example.com",
        "address": "Bani Park, Jaipur",
        "lat": 26.9287, "lng": 75.7946
    }
]

def check_image_url(url: str) -> bool:
    """Returns True if the URL returns 200 and has image content type within a short timeout."""
    try:
        r = requests.head(url, timeout=3, allow_redirects=True)
        if r.status_code == 200 and r.headers.get("Content-Type", "").startswith("image/"):
            return True
        r = requests.get(url, timeout=3, stream=True)
        return r.status_code == 200 and r.headers.get("Content-Type", "").startswith("image/")
    except Exception:
        return False

async def get_or_create_sellers():
    """Ensure the 6 dummy Jaipur sellers exist and return their ObjectIds/docs."""
    users_col = get_users_collection()
    shops_col = get_shops_collection()
    
    sellers_docs = []
    default_password = get_password_hash("password")
    
    for s in JAIPUR_SELLERS:
        existing = await users_col.find_one({"email": s["email"]})
        if existing:
            sellers_docs.append(existing)
        else:
            user_doc = {
                "email": s["email"],
                "name": s["name"],
                "role": "seller",
                "phone": f"9{random.randint(100000000, 999999999)}",
                "hashed_password": default_password,
                "is_active": True,
                "created_at": datetime.utcnow()
            }
            res = await users_col.insert_one(user_doc)
            user_doc["_id"] = res.inserted_id
            sellers_docs.append(user_doc)
            
            # Also create corresponding shop doc for them if needed
            shop_doc = {
                "owner_id": str(user_doc["_id"]),
                "name": s["name"],
                "address": s["address"],
                "location": {
                    "type": "Point",
                    "coordinates": [s["lng"], s["lat"]]
                },
                "status": "active"
            }
            await shops_col.update_one({"owner_id": str(user_doc["_id"])}, {"$setOnInsert": shop_doc}, upsert=True)
            print(f"Created dummy seller: {s['name']}")
    return sellers_docs

async def enrich_with_ai(raw_product: dict) -> dict:
    """Uses Gemini to clean the product name, generate description, price, and exact category."""
    prompt = f"""You are a data cleaning expert for an Indian instant grocery app.
I have a raw product from an open API. Validate it and enrich it.
RAW DATA:
Name: {raw_product.get('product_name')}
Brand: {raw_product.get('brand')}
Categories: {raw_product.get('categories')}
Keywords: {raw_product.get('keywords')}

YOUR TASK:
1. "name": Clean the product name into a professional title (e.g. "maggi 2 minute noodles masala pack" -> "Maggi 2-Minute Masala Noodles"). If it's a generic unbranded item without context, infer a readable name.
2. "description": Write exactly 2 engaging sentences describing the product. 
3. "category": Choose the SINGLE BEST category EXACTLY from this list: {CATEGORIES}. Do not deviate from these choices.
4. "price": Estimate a realistic price in INR (Rupees) for this item (integer or float). Examples: Maggi: 14, Pepsi 500ml: 40, Shampoo: 180.
5. "tags": 3 to 5 lowercase search tags.

Return ONLY valid JSON format.
Example:
{{
  "name": "Coca-Cola Classic (500ml)",
  "description": "The world's favorite sparkling beverage, delivering a refreshing and uplifting taste with every sip. Served perfectly chilled for maximum enjoyment.",
  "category": "Beverages",
  "price": 40.0,
  "tags": ["soft drink", "coke", "soda", "cold drink"]
}}"""

    try:
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
        print(f"  [!] AI Enrichment failed for '{raw_product.get('product_name')}': {e}. Using fallback data.")
        # Fallback category logic: Use the one in raw_product if it's in CATEGORIES, else Groceries
        raw_cat = raw_product.get("categories", "Groceries")
        fallback_cat = "Groceries"
        for c in CATEGORIES:
            if c.lower() in raw_cat.lower():
                fallback_cat = c
                break

        return {
            "name": raw_product.get("product_name").title() if raw_product.get("product_name") else "Imported Item",
            "description": "High-quality premium product.",
            "category": fallback_cat,
            "price": random.randint(50, 500),
            "tags": ["imported", "grocery"]
        }
    return None

async def import_products():
    print("Starting product import...")
    sellers = await get_or_create_sellers()
    if not sellers:
        print("Failed to initialize sellers.")
        return

    products_col = get_products_collection()
    
    products = []
    
    products = []
    
    print("\n--- Fetching diverse products from DummyJSON ---")
    try:
        r = requests.get("https://dummyjson.com/products?limit=0", timeout=10)
        if r.status_code == 200:
            data = r.json()
            fetched_items = data.get("products", [])
            for item in fetched_items:
                if item.get("images"):
                    products.append({
                        "code": item.get("sku", str(item.get("id"))),
                        "product_name": item.get("title"),
                        "brands": item.get("brand", "Generic"),
                        "image_url": item.get("images")[0],
                        "categories": item.get("category", "")
                    })
            print(f"  [✓] Successfully fetched {len(products)} items from DummyJSON")
    except Exception as e:
        print(f"  [!] DummyJSON failed: {e}")
        
    medical_items = [
        {"code": "MED001", "product_name": "Paracetamol 500mg Tablets", "brands": "Crocin", "image_url": "https://cdn-icons-png.flaticon.com/512/2862/2862892.png", "categories": "Health & Wellness"},
        {"code": "MED002", "product_name": "Adhesive Bandages", "brands": "Band-Aid", "image_url": "https://cdn-icons-png.flaticon.com/512/883/883407.png", "categories": "Health & Wellness"},
        {"code": "MED003", "product_name": "Cough Syrup", "brands": "Benadryl", "image_url": "https://cdn-icons-png.flaticon.com/512/3063/3063075.png", "categories": "Health & Wellness"},
        {"code": "MED004", "product_name": "Antiseptic Liquid", "brands": "Dettol", "image_url": "https://cdn-icons-png.flaticon.com/512/2862/2862892.png", "categories": "Health & Wellness"},
        {"code": "MED005", "product_name": "Digital Thermometer", "brands": "Omron", "image_url": "https://cdn-icons-png.flaticon.com/512/883/883407.png", "categories": "Health & Wellness"},
        {"code": "MED006", "product_name": "Vitamin C Zinc Supplements", "brands": "Limcee", "image_url": "https://cdn-icons-png.flaticon.com/512/2862/2862892.png", "categories": "Health & Wellness"},
        {"code": "MED007", "product_name": "Pain Relief Spray", "brands": "Volini", "image_url": "https://cdn-icons-png.flaticon.com/512/3063/3063075.png", "categories": "Health & Wellness"},
        {"code": "MED008", "product_name": "ORS Powder", "brands": "Electral", "image_url": "https://cdn-icons-png.flaticon.com/512/2862/2862892.png", "categories": "Health & Wellness"},
        {"code": "MED009", "product_name": "Digestive Drops", "brands": "Pudin Hara", "image_url": "https://cdn-icons-png.flaticon.com/512/883/883407.png", "categories": "Health & Wellness"},
        {"code": "MED010", "product_name": "First Aid Kit", "brands": "Generic", "image_url": "https://cdn-icons-png.flaticon.com/512/3063/3063075.png", "categories": "Health & Wellness"}
    ]
    
    indian_items = [
        {"code": "IND001", "product_name": "Maggi 2-Minute Noodles Masala", "brands": "Nestle", "image_url": "https://m.media-amazon.com/images/I/81pI7l6L+EL._SL1500_.jpg", "categories": "Snacks"},
        {"code": "IND002", "product_name": "Kurkure Masala Munch", "brands": "PepsiCo", "image_url": "https://m.media-amazon.com/images/I/71X8kE-D5aL._SL1500_.jpg", "categories": "Snacks"},
        {"code": "IND003", "product_name": "Lay's Magic Masala Chips", "brands": "PepsiCo", "image_url": "https://m.media-amazon.com/images/I/71f-5m0qW8L._SL1500_.jpg", "categories": "Snacks"},
        {"code": "IND004", "product_name": "Haldiram's Bhujia Sev", "brands": "Haldiram", "image_url": "https://m.media-amazon.com/images/I/81x59W2P9yL._SL1500_.jpg", "categories": "Snacks"},
        {"code": "IND005", "product_name": "Amul Butter (500g)", "brands": "Amul", "image_url": "https://m.media-amazon.com/images/I/61S+p6iXfLL._SL1000_.jpg", "categories": "Dairy"},
        {"code": "IND006", "product_name": "Aashirvaad Superior MP Atta (5kg)", "brands": "ITC", "image_url": "https://m.media-amazon.com/images/I/81mFpW+6p2L._SL1500_.jpg", "categories": "Groceries"},
        {"code": "IND007", "product_name": "Tata Salt (1kg)", "brands": "Tata", "image_url": "https://m.media-amazon.com/images/I/61kY8y7n5KL._SL1500_.jpg", "categories": "Groceries"},
        {"code": "IND008", "product_name": "Parle-G Gold Biscuits", "brands": "Parle", "image_url": "https://m.media-amazon.com/images/I/71YyqWd7vCL._SL1500_.jpg", "categories": "Snacks"},
        {"code": "IND009", "product_name": "Red Label Tea (500g)", "brands": "Brook Bond", "image_url": "https://m.media-amazon.com/images/I/61O+0Z4I3RL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "IND010", "product_name": "Fortune Soya Health Oil (1L)", "brands": "Adani Wilmar", "image_url": "https://m.media-amazon.com/images/I/61R5Wv2C45L._SL1000_.jpg", "categories": "Groceries"},
        {"code": "IND011", "product_name": "Patanjali Honey (500g)", "brands": "Patanjali", "image_url": "https://m.media-amazon.com/images/I/61X-H2BqBHL._SL1500_.jpg", "categories": "Groceries"},
        {"code": "IND012", "product_name": "Dabur Honey (400g)", "brands": "Dabur", "image_url": "https://m.media-amazon.com/images/I/61OnG0WfBCL._SL1500_.jpg", "categories": "Groceries"},
        {"code": "IND013", "product_name": "Maggi Pazzta Masala Penne", "brands": "Nestle", "image_url": "https://m.media-amazon.com/images/I/81L6pI6WpLL._SL1500_.jpg", "categories": "Snacks"},
        {"code": "IND014", "product_name": "Knorr Mixed Vegetable Soup", "brands": "Hindustan Unilever", "image_url": "https://m.media-amazon.com/images/I/71oX6uP0yML._SL1500_.jpg", "categories": "Snacks"},
        {"code": "IND015", "product_name": "Amul Taza Milk (1L)", "brands": "Amul", "image_url": "https://m.media-amazon.com/images/I/61W+f3H2rFL._SL1000_.jpg", "categories": "Dairy"},
        {"code": "IND016", "product_name": "Paper Boat Aamras Mango Juice", "brands": "Hector Beverages", "image_url": "https://m.media-amazon.com/images/I/61G7Z4uS8RL._SL1500_.jpg", "categories": "Beverages"},
        {"code": "IND017", "product_name": "Frooti Mango Drink (1.2L)", "brands": "Parle Agro", "image_url": "https://m.media-amazon.com/images/I/61hH2D6fSLL._SL1500_.jpg", "categories": "Beverages"},
        {"code": "IND018", "product_name": "Cadbury Dairy Milk (Single Pack)", "brands": "Mondelez", "image_url": "https://m.media-amazon.com/images/I/61b7U8P3OML._SL1000_.jpg", "categories": "Snacks"},
        {"code": "IND019", "product_name": "Hide & Seek Chocolate Chip Cookies", "brands": "Parle", "image_url": "https://m.media-amazon.com/images/I/81A7oJ6fSLL._SL1500_.jpg", "categories": "Snacks"},
        {"code": "IND020", "product_name": "Parle Monaco Salted Biscuits", "brands": "Parle", "image_url": "https://m.media-amazon.com/images/I/81h9hS-D8L._SL1500_.jpg", "categories": "Snacks"},
        {"code": "IND021", "product_name": "Pepsi Soft Drink (600ml)", "brands": "PepsiCo", "image_url": "https://m.media-amazon.com/images/I/613n-O9fB3L._SL1500_.jpg", "categories": "Beverages"},
        {"code": "IND022", "product_name": "Coca-Cola (600ml)", "brands": "Coca-Cola", "image_url": "https://m.media-amazon.com/images/I/61W9oB69P3L._SL1500_.jpg", "categories": "Beverages"},
        {"code": "IND023", "product_name": "Sprite (600ml)", "brands": "Coca-Cola", "image_url": "https://m.media-amazon.com/images/I/61Z6vO9M3LL._SL1500_.jpg", "categories": "Beverages"},
        {"code": "IND024", "product_name": "Maaza Mango Drink (600ml)", "brands": "Coca-Cola", "image_url": "https://m.media-amazon.com/images/I/61f-D6D6kPL._SL1500_.jpg", "categories": "Beverages"},
        {"code": "IND025", "product_name": "Bingo Mad Angles Achaari Masti", "brands": "ITC", "image_url": "https://m.media-amazon.com/images/I/81G-P-r6rDL._SL1500_.jpg", "categories": "Snacks"},
        {"code": "IND026", "product_name": "Cadbury 5 Star Chocolate", "brands": "Mondelez", "image_url": "https://m.media-amazon.com/images/I/61v3Z3-o8vL._SL1000_.jpg", "categories": "Snacks"},
        {"code": "IND027", "product_name": "Nestle Munch Chocolate Bar", "brands": "Nestle", "image_url": "https://m.media-amazon.com/images/I/61b7U8P3OML._SL1000_.jpg", "categories": "Snacks"},
        {"code": "IND028", "product_name": "Cadbury Perk Chocolate", "brands": "Mondelez", "image_url": "https://m.media-amazon.com/images/I/61b7U8P3OML._SL1000_.jpg", "categories": "Snacks"},
        {"code": "IND029", "product_name": "Surf Excel Matic Front Load Liquid", "brands": "Hindustan Unilever", "image_url": "https://m.media-amazon.com/images/I/61-9O3r8S3L._SL1000_.jpg", "categories": "Household"},
        {"code": "IND030", "product_name": "Vim Dishwash Liquid Gel", "brands": "Hindustan Unilever", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Household"},
        {"code": "IND031", "product_name": "Harpic Disinfectant Toilet Cleaner", "brands": "Reckitt", "image_url": "https://m.media-amazon.com/images/I/61-vO3r8S3L._SL1000_.jpg", "categories": "Household"},
        {"code": "IND032", "product_name": "Colin Glass Cleaner", "brands": "Reckitt", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Household"},
        {"code": "IND033", "product_name": "Lizol Disinfectant Floor Cleaner", "brands": "Reckitt", "image_url": "https://m.media-amazon.com/images/I/61-vO3r8S3L._SL1000_.jpg", "categories": "Household"},
        {"code": "IND034", "product_name": "Comfort Fabric Conditioner", "brands": "Hindustan Unilever", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Household"},
        {"code": "IND035", "product_name": "Dove Cream Beauty Bar", "brands": "Hindustan Unilever", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Personal Care"},
        {"code": "IND036", "product_name": "Sunsilk Stunning Black Shine Shampoo", "brands": "Hindustan Unilever", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Personal Care"},
        {"code": "IND037", "product_name": "Pears Pure & Gentle Soap", "brands": "Hindustan Unilever", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Personal Care"},
        {"code": "IND038", "product_name": "Dettol Original Germ Protection Soap", "brands": "Reckitt", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Personal Care"},
        {"code": "IND039", "product_name": "Glow & Lovely Advanced Multivitamin", "brands": "Hindustan Unilever", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Personal Care"},
        {"code": "IND040", "product_name": "Lifebuoy Total 10 Soap", "brands": "Hindustan Unilever", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Personal Care"},
        {"code": "IND041", "product_name": "Pampers Baby Dry Diapers", "brands": "P&G", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Baby Products"},
        {"code": "IND042", "product_name": "MamyPoko Pants Standard", "brands": "Unicharm", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Baby Products"},
        {"code": "IND043", "product_name": "Everest Chicken Masala", "brands": "Everest", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Groceries"},
        {"code": "IND044", "product_name": "Catch Turmeric Powder (200g)", "brands": "Catch", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Groceries"},
        {"code": "IND045", "product_name": "Nescafé Classic Coffee (100g)", "brands": "Nestle", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "IND046", "product_name": "Bru Instant Coffee (100g)", "brands": "Hindustan Unilever", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "IND047", "product_name": "Bournvita Chocolate Health Drink", "brands": "Mondelez", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "IND048", "product_name": "Horlicks Health & Nutrition Drink", "brands": "Unilever", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "IND049", "product_name": "Boost Health Drink", "brands": "Unilever", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "IND050", "product_name": "Complan Royale Chocolate", "brands": "Zydus Wellness", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "IND051", "product_name": "Amul Kool Koko (200ml)", "brands": "Amul", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "IND052", "product_name": "Minute Maid Pulpy Orange", "brands": "Coca-Cola", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "IND053", "product_name": "Dettol Antiseptic Disinfectant Liquid", "brands": "Reckitt", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Household"},
        {"code": "IND054", "product_name": "Pears Pure & Gentle Body Wash", "brands": "Hindustan Unilever", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Personal Care"},
        {"code": "IND055", "product_name": "Himalaya Purifying Neem Face Wash", "brands": "Himalaya Wellness", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Personal Care"},
        {"code": "IND056", "product_name": "Colgate Strong Teeth Toothpaste", "brands": "Colgate", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Personal Care"},
        {"code": "IND057", "product_name": "Pepsodent G Gum Care Toothpaste", "brands": "Hindustan Unilever", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Personal Care"},
        {"code": "IND058", "product_name": "Sensodyne Fresh Gel Toothpaste", "brands": "GSK", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Personal Care"},
        {"code": "IND059", "product_name": "Dant Kanti Toothpaste", "brands": "Patanjali", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Personal Care"},
        {"code": "IND060", "product_name": "Close Up Everfresh Red Gel", "brands": "Hindustan Unilever", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Personal Care"},
        {"code": "IND061", "product_name": "Vaseline Deep Moisture Lotion", "brands": "Hindustan Unilever", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Personal Care"},
        {"code": "IND062", "product_name": "Nivea Soft Light Cream", "brands": "Nivea", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Personal Care"},
        {"code": "IND063", "product_name": "Ponds Super Light Gel", "brands": "Hindustan Unilever", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Personal Care"},
        {"code": "IND064", "product_name": "Fair & Lovely Face Wash", "brands": "Hindustan Unilever", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Personal Care"},
        {"code": "IND065", "product_name": "Head & Shoulders Anti Dandruff", "brands": "P&G", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Personal Care"},
        {"code": "IND066", "product_name": "Pantene Hair Fall Control Shampoo", "brands": "P&G", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Personal Care"},
        {"code": "IND067", "product_name": "L'Oreal Paris Total Repair 5", "brands": "L'Oreal", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Personal Care"},
        {"code": "IND068", "product_name": "Tresemme Keratin Smooth Shampoo", "brands": "Hindustan Unilever", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Personal Care"},
        {"code": "IND069", "product_name": "Johnson's Baby Powder", "brands": "Johnson & Johnson", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Baby Products"},
        {"code": "IND070", "product_name": "Johnson's Baby Shampoo", "brands": "Johnson & Johnson", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Baby Products"},
        {"code": "IND071", "product_name": "Himalaya Baby Lotion", "brands": "Himalaya Wellness", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Baby Products"},
        {"code": "IND072", "product_name": "Sebamed Baby Cream", "brands": "Sebamed", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Baby Products"}
    ]
    
    bakery_items = [
        {"code": "BAK001", "product_name": "Britannia Fruit Cake", "brands": "Britannia", "image_url": "https://m.media-amazon.com/images/I/71X8kE-D5aL._SL1500_.jpg", "categories": "Bakery & Cakes"},
        {"code": "BAK002", "product_name": "Britannia Milk Bikis", "brands": "Britannia", "image_url": "https://m.media-amazon.com/images/I/71f-5m0qW8L._SL1500_.jpg", "categories": "Bakery & Cakes"},
        {"code": "BAK003", "product_name": "Britannia Good Day Cashew", "brands": "Britannia", "image_url": "https://m.media-amazon.com/images/I/81x59W2P9yL._SL1500_.jpg", "categories": "Bakery & Cakes"},
        {"code": "BAK004", "product_name": "Harvest Gold White Bread", "brands": "Harvest Gold", "image_url": "https://m.media-amazon.com/images/I/61S+p6iXfLL._SL1000_.jpg", "categories": "Bakery & Cakes"},
        {"code": "BAK005", "product_name": "Harvest Gold Brown Bread", "brands": "Harvest Gold", "image_url": "https://m.media-amazon.com/images/I/81mFpW+6p2L._SL1500_.jpg", "categories": "Bakery & Cakes"},
        {"code": "BAK006", "product_name": "Pillsbury Choco Cookie Cake", "brands": "Pillsbury", "image_url": "https://m.media-amazon.com/images/I/61kY8y7n5KL._SL1500_.jpg", "categories": "Bakery & Cakes"},
        {"code": "BAK007", "product_name": "Britannia Premium Bake Rusk", "brands": "Britannia", "image_url": "https://m.media-amazon.com/images/I/71YyqWd7vCL._SL1500_.jpg", "categories": "Bakery & Cakes"},
        {"code": "BAK008", "product_name": "Britannia Veg Pav (Pack of 4)", "brands": "Britannia", "image_url": "https://m.media-amazon.com/images/I/61O+0Z4I3RL._SL1000_.jpg", "categories": "Bakery & Cakes"},
        {"code": "BAK009", "product_name": "Britannia Little Hearts Biscuits", "brands": "Britannia", "image_url": "https://m.media-amazon.com/images/I/61R5Wv2C45L._SL1000_.jpg", "categories": "Bakery & Cakes"},
        {"code": "BAK010", "product_name": "Britannia Bourbon Biscuits", "brands": "Britannia", "image_url": "https://m.media-amazon.com/images/I/61X-H2BqBHL._SL1500_.jpg", "categories": "Bakery & Cakes"},
        {"code": "BAK011", "product_name": "Blueberry Muffins (Pack of 2)", "brands": "Generic", "image_url": "https://cdn-icons-png.flaticon.com/512/3063/3063075.png", "categories": "Bakery & Cakes"},
        {"code": "BAK012", "product_name": "Choco Chip Brownies", "brands": "Generic", "image_url": "https://cdn-icons-png.flaticon.com/512/3063/3063075.png", "categories": "Bakery & Cakes"},
        {"code": "BAK013", "product_name": "Garlic Bread Loaf", "brands": "Generic", "image_url": "https://cdn-icons-png.flaticon.com/512/61S+p6iXfLL._SL1000_.jpg", "categories": "Bakery & Cakes"},
        {"code": "BAK014", "product_name": "Plain Croissants (Pack of 2)", "brands": "Generic", "image_url": "https://cdn-icons-png.flaticon.com/512/61kY8y7n5KL._SL1500_.jpg", "categories": "Bakery & Cakes"},
        {"code": "BAK015", "product_name": "Cinnamon Rolls with Icing", "brands": "Generic", "image_url": "https://cdn-icons-png.flaticon.com/512/71YyqWd7vCL._SL1500_.jpg", "categories": "Bakery & Cakes"}
    ]

    fresh_items = [
        {"code": "FRE001", "product_name": "Fresh Red Apples (1kg)", "brands": "Farm Fresh", "image_url": "https://m.media-amazon.com/images/I/91p6PAnzGvL._SL1500_.jpg", "categories": "Fruits & Vegetables"},
        {"code": "FRE002", "product_name": "Robust Bananas (Bunch of 6)", "brands": "Farm Fresh", "image_url": "https://m.media-amazon.com/images/I/71X8kE-D5aL._SL1500_.jpg", "categories": "Fruits & Vegetables"},
        {"code": "FRE003", "product_name": "Nagpur Oranges (1kg)", "brands": "Farm Fresh", "image_url": "https://m.media-amazon.com/images/I/71f-5m0qW8L._SL1500_.jpg", "categories": "Fruits & Vegetables"},
        {"code": "FRE004", "product_name": "Fresh Potatoes (1kg)", "brands": "Farm Fresh", "image_url": "https://m.media-amazon.com/images/I/81x59W2P9yL._SL1500_.jpg", "categories": "Fruits & Vegetables"},
        {"code": "FRE005", "product_name": "Hybrid Tomatoes (500g)", "brands": "Farm Fresh", "image_url": "https://m.media-amazon.com/images/I/61S+p6iXfLL._SL1000_.jpg", "categories": "Fruits & Vegetables"},
        {"code": "FRE006", "product_name": "Fresh Onions (1kg)", "brands": "Farm Fresh", "image_url": "https://m.media-amazon.com/images/I/81mFpW+6p2L._SL1500_.jpg", "categories": "Fruits & Vegetables"},
        {"code": "FRE007", "product_name": "Spinach Bunch (250g)", "brands": "Farm Fresh", "image_url": "https://m.media-amazon.com/images/I/61kY8y7n5KL._SL1500_.jpg", "categories": "Fruits & Vegetables"},
        {"code": "FRE008", "product_name": "Fresh Carrots (500g)", "brands": "Farm Fresh", "image_url": "https://m.media-amazon.com/images/I/71YyqWd7vCL._SL1500_.jpg", "categories": "Fruits & Vegetables"},
        {"code": "FRE009", "product_name": "Amul Fresh Paneer (200g)", "brands": "Amul", "image_url": "https://m.media-amazon.com/images/I/61O+0Z4I3RL._SL1000_.jpg", "categories": "Dairy"},
        {"code": "FRE010", "product_name": "Amul Masti Spiced Buttermilk", "brands": "Amul", "image_url": "https://m.media-amazon.com/images/I/61R5Wv2C45L._SL1000_.jpg", "categories": "Dairy"},
        {"code": "FRE011", "product_name": "Amul Taaza Milk (500ml)", "brands": "Amul", "image_url": "https://m.media-amazon.com/images/I/61X-H2BqBHL._SL1500_.jpg", "categories": "Dairy"},
        {"code": "FRE012", "product_name": "Mother Dairy Curd (400g)", "brands": "Mother Dairy", "image_url": "https://m.media-amazon.com/images/I/61OnG0WfBCL._SL1500_.jpg", "categories": "Dairy"},
        {"code": "FRE013", "product_name": "Britannia Cheese Slices (100g)", "brands": "Britannia", "image_url": "https://m.media-amazon.com/images/I/81L6pI6WpLL._SL1500_.jpg", "categories": "Dairy"},
        {"code": "FRE014", "product_name": "Farm Fresh White Eggs (6 pcs)", "brands": "Farm Fresh", "image_url": "https://m.media-amazon.com/images/I/71oX6uP0yML._SL1500_.jpg", "categories": "Meats & Seafood"},
        {"code": "FRE015", "product_name": "Fresh Chicken Breast (500g)", "brands": "Quality Meats", "image_url": "https://m.media-amazon.com/images/I/61W+f3H2rFL._SL1000_.jpg", "categories": "Meats & Seafood"},
        {"code": "FRE016", "product_name": "Premium Mutton Keema (500g)", "brands": "Quality Meats", "image_url": "https://m.media-amazon.com/images/I/61G7Z4uS8RL._SL1500_.jpg", "categories": "Meats & Seafood"},
        {"code": "FRE017", "product_name": "Fresh Rohu Fish (Cut - 500g)", "brands": "Seafood Direct", "image_url": "https://m.media-amazon.com/images/I/61hH2D6fSLL._SL1500_.jpg", "categories": "Meats & Seafood"}
    ]

    beverage_items = [
        {"code": "BEV001", "product_name": "Red Bull Energy Drink (250ml)", "brands": "Red Bull", "image_url": "https://m.media-amazon.com/images/I/61-9O3r8S3L._SL1000_.jpg", "categories": "Beverages"},
        {"code": "BEV002", "product_name": "Monster Energy Ultra (500ml)", "brands": "Monster Energy", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "BEV003", "product_name": "Bisleri Packaged Water (1L)", "brands": "Bisleri", "image_url": "https://m.media-amazon.com/images/I/61-vO3r8S3L._SL1000_.jpg", "categories": "Beverages"},
        {"code": "BEV004", "product_name": "Kinley Sparkling Water (500ml)", "brands": "Coca-Cola", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "BEV005", "product_name": "Real Fruit Power Orange Juice", "brands": "Dabur", "image_url": "https://m.media-amazon.com/images/I/61-vO3r8S3L._SL1000_.jpg", "categories": "Beverages"},
        {"code": "BEV006", "product_name": "Real Fruit Power Mixed Fruit", "brands": "Dabur", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "BEV007", "product_name": "Tropicana 100% Apple Juice", "brands": "PepsiCo", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "BEV008", "product_name": "B-Fizz Sparkling Malt Drink", "brands": "Parle Agro", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "BEV009", "product_name": "Appy Fizz (600ml)", "brands": "Parle Agro", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "BEV010", "product_name": "Sting Energy Drink (250ml)", "brands": "PepsiCo", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "BEV011", "product_name": "Thums Up Soft Drink (750ml)", "brands": "Coca-Cola", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "BEV012", "product_name": "Mountain Dew (750ml)", "brands": "PepsiCo", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "BEV013", "product_name": "Limca Soft Drink (750ml)", "brands": "Coca-Cola", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "BEV014", "product_name": "Fanta Orange (750ml)", "brands": "Coca-Cola", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "BEV015", "product_name": "Paper Boat Jaljeera (250ml)", "brands": "Hector Beverages", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "BEV016", "product_name": "Paper Boat Thandai (250ml)", "brands": "Hector Beverages", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "BEV017", "product_name": "Gatorade Blue Bolt (500ml)", "brands": "PepsiCo", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "BEV018", "product_name": "Aquafina Packaged Water (1L)", "brands": "PepsiCo", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "BEV019", "product_name": "Himalayan Mineral Water (1L)", "brands": "Tata Consumer", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"},
        {"code": "BEV020", "product_name": "Schweppes Ginger Ale (300ml)", "brands": "Coca-Cola", "image_url": "https://m.media-amazon.com/images/I/61z-vS9kKLL._SL1000_.jpg", "categories": "Beverages"}
    ]
    
    products = medical_items + indian_items + bakery_items + fresh_items + beverage_items + products

    target_products = 550
    total_inserted = 0
 
    for p in products:
        if total_inserted >= target_products:
            break
            
        code = p.get("code")
        name = p.get("product_name")
        image_url = p.get("image_url")
        
        if not code or not name or not image_url:
            continue

        # Check if this barcode already exists in DB (even for one seller)
        existing = await products_col.find_one({"barcode": code})
        if existing:
            print(f"  [-] Skipping {code} - already in DB.")
            continue

        print(f"  [+] Processing: {name} ({code})")
        
        # Ensure image_url is valid, otherwise use fallback
        if not image_url or "flaticon.com" in image_url or "example.com" in image_url:
            print(f"      -> Missing or placeholder image, using fallback.")
            image_url = FALLBACK_IMAGE
        elif not code.startswith(("IND", "MED", "BAK", "FRE", "BEV")): # Skip check for our known high-load hardcoded prefixes
            if not check_image_url(image_url):
                print(f"      -> Dead image URL, using fallback.")
                image_url = FALLBACK_IMAGE

        raw_data = {
            "product_name": name,
            "brand": p.get("brands", ""),
            "categories": p.get("categories", ""),
            "keywords": p.get("_keywords", [])
        }
        
        enriched = await enrich_with_ai(raw_data)
        if not enriched:
            continue
            
        print(f"      => AI returned Name: {enriched.get('name')} | Price: ₹{enriched.get('price')} | Cat: {enriched.get('category')}")
        
        # Filter only to our JAIPUR sellers to ensure we insert data correctly
        jaipur_emails = [s["email"] for s in JAIPUR_SELLERS]
        valid_sellers = [s for s in sellers if s.get("email") in jaipur_emails]
        
        # Select exactly 1 random seller to assign this product to
        assigned_sellers = random.sample(valid_sellers, 1)
        
        # Precalculate embedding
        embed_str = f"{enriched.get('name')} {enriched.get('description')} {enriched.get('category')} {' '.join(enriched.get('tags', []))}"
        embedding = embed_text(embed_str)
        
        base_doc = {
            "name": enriched.get("name"),
            "description": enriched.get("description"),
            "price": float(enriched.get("price", 100.0)),
            "category": enriched.get("category", "Groceries"),
            "barcode": code,
            "unit": "1 pc",
            "image_url": image_url,
            "tags": enriched.get("tags", []),
            "embedding": embedding,
            "rating": round(random.uniform(4.0, 5.0), 1),
            "total_sold": random.randint(0, 500),
            "mrp": float(enriched.get("price", 100.0)) * random.choice([1.0, 1.1, 1.2]),
            "auto_imported": True,
            "created_at": datetime.utcnow()
        }
        
        inserted_count = 0
        for seller in assigned_sellers:
            # Find matching shop from JAIPUR_SELLERS info
            shop_info = next((s for s in JAIPUR_SELLERS if s["email"] == seller["email"]), None)
            if not shop_info:
                continue
                
            doc = base_doc.copy()
            doc["seller_id"] = str(seller["_id"])
            doc["seller_name"] = seller["name"]
            doc["stock"] = random.randint(10, 200)
            doc["location"] = {
                "type": "Point",
                "coordinates": [shop_info["lng"], shop_info["lat"]]
            }
            doc["address"] = shop_info["address"]
            
            await products_col.insert_one(doc)
            inserted_count += 1
        
        if inserted_count > 0:
            print(f"      => Inserted for {inserted_count} sellers.")
            total_inserted += 1

    print(f"\nImport job complete! Inserted {total_inserted} distinct products across multiple sellers.")

if __name__ == "__main__":
    asyncio.run(import_products())
