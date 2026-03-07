import asyncio
import os
import sys
import requests
import random
import time
from urllib.parse import quote
from dotenv import load_dotenv
import google.generativeai as genai

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_products_collection

load_dotenv()

# Configure Gemini for relevance check
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Configure Gemini for relevance check (DISABLED DUE TO ENV ISSUES WITH PYTHON 3.14)
# if GEMINI_API_KEY:
#     genai.configure(api_key=GEMINI_API_KEY)
#     try:
#         model = genai.GenerativeModel('gemini-1.5-flash')
#     except:
#         model = genai.GenerativeModel('gemini-pro')
# else:
#     model = None
model = None

# Public Search APIs / Endpoints
OFF_SEARCH_API = "https://world.openfoodfacts.org/cgi/search.pl"
OBF_SEARCH_API = "https://world.openbeautyfacts.org/cgi/search.pl"

HEADERS = {
    "User-Agent": "SmarterBlinkit/1.0 (contact@smarterblinkit.com)"
}

# Unsplash Fallback Pool (High Quality)
UNSPLASH_FALLBACKS = {
    "Groceries": "https://images.unsplash.com/photo-1542838132-92c53300491e?q=80&w=1000&auto=format&fit=crop",
    "Beverages": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?q=80&w=1000&auto=format&fit=crop",
    "Personal Care": "https://images.unsplash.com/photo-1556228720-195a672e8a03?q=80&w=1000&auto=format&fit=crop",
    "Electronics": "https://images.unsplash.com/photo-1498049794561-7780e7231661?q=80&w=1000&auto=format&fit=crop",
    "Household": "https://images.unsplash.com/photo-1581578731548-c64695cc6954?q=80&w=1000&auto=format&fit=crop",
    "Fruits & Vegetables": "https://images.unsplash.com/photo-1610348725531-843dff563e2c?q=80&w=1000&auto=format&fit=crop",
    "Meats & Seafood": "https://images.unsplash.com/photo-1607623273562-b9e70f61284d?q=80&w=1000&auto=format&fit=crop",
    "Bakery & Cakes": "https://images.unsplash.com/photo-1509440159596-0249088772ff?q=80&w=1000&auto=format&fit=crop",
    "General": "https://images.unsplash.com/photo-1542838132-92c53300491e?q=80&w=1000&auto=format&fit=crop"
}

# HIGH ACCURACY KEYWORD MAPPING (Unsplash)
KEYWORD_MAPPING = {
    "shampoo": "https://images.unsplash.com/photo-1585232351009-aa87416fca90?q=80&w=1000&auto=format&fit=crop",
    "soap": "https://images.unsplash.com/photo-1600857544200-b2f666a9a234?q=80&w=1000&auto=format&fit=crop",
    "cream": "https://images.unsplash.com/photo-1556228720-195a672e8a03?q=80&w=1000&auto=format&fit=crop",
    "lipstick": "https://images.unsplash.com/photo-1586495764447-c0f9946bc77a?q=80&w=1000&auto=format&fit=crop",
    "palette": "https://images.unsplash.com/photo-1512496011931-a20412854972?q=80&w=1000&auto=format&fit=crop",
    "mascara": "https://images.unsplash.com/photo-1591360236630-4eb9b3c34fbd?q=80&w=1000&auto=format&fit=crop",
    "perfume": "https://images.unsplash.com/photo-1541643600914-78b084683601?q=80&w=1000&auto=format&fit=crop",
    "nail polish": "https://images.unsplash.com/photo-1522337363644-329141522fbb?q=80&w=1000&auto=format&fit=crop",
    "eye care": "https://images.unsplash.com/photo-1583209814683-c023dd2f3ca3?q=80&w=1000&auto=format&fit=crop",
    "face wash": "https://images.unsplash.com/photo-1556229167-73191319a992?q=80&w=1000&auto=format&fit=crop",
    "oil": "https://images.unsplash.com/photo-1474979266404-7eaacabc87c5?q=80&w=1000&auto=format&fit=crop",
    "powder": "https://images.unsplash.com/photo-1556229174-5e42a09e45af?q=80&w=1000&auto=format&fit=crop",
    "serum": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?q=80&w=1000&auto=format&fit=crop"
}

async def fix_product_images(dry_run=False):
    products_col = get_products_collection()
    
    query = {
        "$or": [
            {"image_url": {"$regex": "dummyjson.com"}},
            {"image_url": {"$regex": "example.com"}},
            {"image_url": {"$regex": "flaticon.com"}},
            {"image_url": None},
            {"image_url": ""}
        ]
    }
    
    total_to_fix = await products_col.count_documents(query)
    print(f"\n--- Optimized Product Image Fixer ---")
    if dry_run:
        print("!!! DRY RUN MODE !!!")
    print(f"Targeting {total_to_fix} products...")
    
    fixed_count = 0
    
    cursor = products_col.find(query)
    
    async for product in cursor:
        name = product.get("name", "").lower()
        category = product.get("category", "General")
        
        print(f"🔍 {product.get('name')}...", end=" ", flush=True)
        
        # 1. KEYWORD MATCHING (Fastest & Reliable)
        new_url = None
        for kw, url in KEYWORD_MAPPING.items():
            if kw in name:
                new_url = url
                break
        
        # 2. IF NO KEYWORD, TRY SEARCH (Limited)
        if not new_url:
            # We skip heavy searching for now to avoid delays, or use a very fast check
            pass
            
        # 3. FALLBACK TO CATEGORY
        if not new_url:
            new_url = UNSPLASH_FALLBACKS.get(category, UNSPLASH_FALLBACKS["General"])

        if new_url:
            if not dry_run:
                await products_col.update_one(
                    {"_id": product["_id"]},
                    {"$set": {"image_url": new_url}}
                )
            print(f" [✓]")
            fixed_count += 1
        else:
            print(f" [✗]")
            
        if dry_run and fixed_count >= 20:
            break

    print(f"\nFinal Fix Job Complete! Total Updated: {fixed_count}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    asyncio.run(fix_product_images(dry_run=args.dry_run))
