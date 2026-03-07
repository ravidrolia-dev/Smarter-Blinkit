import os
import sys
import asyncio
import json

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.recipe_agent import parse_recipe_ingredients
from services.ai.gemini_service import gemini_service

async def debug_flow():
    print("\n=== V4 Flow Debugging ===")
    
    # 1. Test Recipe Parsing with Tricky Names
    meal = "Pizza with Pepperoni (Extra) and cheese"
    print(f"\n[1] Testing Tricky Recipe Parsing for: {meal}")
    
    # We'll monkeypatch gemini_service to see exactly what's happening
    original_generate = gemini_service.generate_content
    
    async def logged_generate(prompt, system_instruction=None):
        print(f"--- AI PROMPT ---\n{prompt}")
        if system_instruction:
            print(f"--- SYSTEM INSTRUCTION ---\n{system_instruction}")
        
        result = await original_generate(prompt, system_instruction)
        print(f"--- RAW AI RESPONSE ---\n{result}")
        return result

    gemini_service.generate_content = logged_generate
    
    res = await parse_recipe_ingredients(meal)
    print(f"\n[Parse Result]: {json.dumps(res, indent=2)}")

    # 2. Test Smart Search Fallback (Generation)
    from services.product_generator import generate_search_products
    query = "Organic Almond Milk"
    print(f"\n[2] Testing Search Generation for: {query}")
    gen_res = await generate_search_products(query)
    print(f"\n[Generation Result]: Found {len(gen_res)} products.")
    for p in gen_res:
        print(f" - {p['name']} (Category: {p.get('category')})")

if __name__ == "__main__":
    asyncio.run(debug_flow())
