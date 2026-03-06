import asyncio
import os
import sys
from tqdm import tqdm
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_products_collection
from services.semantic_search import embed_text

load_dotenv()

async def migrate():
    products_col = get_products_collection()
    
    print("Fetching all products for embedding migration...")
    cursor = products_col.find({"auto_imported": True})
    products = await cursor.to_list(length=2000)
    
    print(f"Found {len(products)} products to update.")
    
    updated_count = 0
    for p in tqdm(products, desc="Updating embeddings"):
        # Create the same string used during import
        text_to_embed = f"{p.get('name', '')} {p.get('description', '')} {p.get('category', '')} {' '.join(p.get('tags', []))}"
        
        try:
            new_embedding = embed_text(text_to_embed)
            await products_col.update_one(
                {"_id": p["_id"]},
                {"$set": {"embedding": new_embedding}}
            )
            updated_count += 1
        except Exception as e:
            print(f"Failed to update {p.get('name')}: {e}")

    print(f"\nMigration complete! {updated_count} products updated with new MPNET embeddings.")

if __name__ == "__main__":
    asyncio.run(migrate())
