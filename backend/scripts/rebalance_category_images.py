import asyncio
import os
import sys
import requests
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_products_collection

load_dotenv()

# HIGH QUALITY CATEGORY FALLBACKS
ENHANCED_FALLBACKS = {
    # Medical / Health
    "Health & Wellness": "https://images.unsplash.com/photo-1584017911766-d451b3d0e843?q=80&w=1000&auto=format&fit=crop", # Pharmacy/Medical
    "Skin-Care": "https://images.unsplash.com/photo-1556228720-195a672e8a03?q=80&w=1000&auto=format&fit=crop", # Skincare
    
    # Electronics
    "Smartphones": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?q=80&w=1000&auto=format&fit=crop", # Smartphone
    "Mobile-Accessories": "https://images.unsplash.com/photo-1584438832468-4424a1bfd841?q=80&w=1000&auto=format&fit=crop", # Tech gadgets
    "Laptops": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?q=80&w=1000&auto=format&fit=crop", # Laptop
    "Tablets": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?q=80&w=1000&auto=format&fit=crop", # Tablet
    
    # Home & Lifestyle
    "Home-Decoration": "https://images.unsplash.com/photo-1513519245088-0e12902e5a38?q=80&w=1000&auto=format&fit=crop", # Interior
    "Furniture": "https://images.unsplash.com/photo-1524758631624-e2822e304c36?q=80&w=1000&auto=format&fit=crop", # Furniture
    
    # Accessories
    "Sunglasses": "https://images.unsplash.com/photo-1572635196237-14b3f281503f?q=80&w=1000&auto=format&fit=crop", # Sunglasses
    "Womens-Watches": "https://images.unsplash.com/photo-1524592094714-0f0654e20314?q=80&w=1000&auto=format&fit=crop", # Watches
    "Mens-Watches": "https://images.unsplash.com/photo-1522312346375-d1a52e2b99b3?q=80&w=1000&auto=format&fit=crop", # Watches
    
    # Fashion
    "Womens-Dresses": "https://images.unsplash.com/photo-1539008835279-434ca39359f4?q=80&w=1000&auto=format&fit=crop",
    "Mens-Shirts": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?q=80&w=1000&auto=format&fit=crop",
}

# The image we want to replace if misaligned
GENERIC_GROCERY_AISLE = "https://images.unsplash.com/photo-1542838132-92c53300491e"

async def rebalance_images(dry_run=False):
    products_col = get_products_collection()
    
    print(f"\n--- Rebalancing Category Images ---")
    if dry_run: print("!!! DRY RUN !!!")
    
    rebalanced_count = 0
    
    # Target products that have the generic grocery aisle image but a different category
    query = {
        "image_url": {"$regex": GENERIC_GROCERY_AISLE},
        "category": {"$nin": ["Groceries", "Fruits & Vegetables", "Fruits", "Vegetables", "Snacks", "Bakery & Cakes"]}
    }
    
    cursor = products_col.find(query)
    total_to_fix = await products_col.count_documents(query)
    print(f"Targeting {total_to_fix} misaligned products...")
    
    async for product in cursor:
        name = product.get("name")
        category = product.get("category")
        
        # New image URL based on category
        new_url = ENHANCED_FALLBACKS.get(category)
        
        # If no specific mapping, we use a slightly better "General Store" image than a vegetable aisle
        if not new_url:
            new_url = "https://images.unsplash.com/photo-1534452203293-494d7ddbf7e0?q=80&w=1000&auto=format&fit=crop" # Generic shop
            
        if not dry_run:
            await products_col.update_one(
                {"_id": product["_id"]},
                {"$set": {"image_url": new_url}}
            )
        
        # print(f"Rebalanced: {name} ({category}) -> {new_url[:40]}...")
        rebalanced_count += 1

    print(f"\nRebalancing Complete! Total Rebalanced: {rebalanced_count}")

if __name__ == "__main__":
    asyncio.run(rebalance_images())
