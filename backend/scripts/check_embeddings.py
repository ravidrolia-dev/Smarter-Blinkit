import os
import sys
import asyncio

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_products_collection

async def check_embeddings():
    print("\n--- Embedding Integrity Check ---")
    products_col = get_products_collection()
    
    total = await products_col.count_documents({})
    missing = await products_col.count_documents({"embedding": {"$exists": False}})
    null_emb = await products_col.count_documents({"embedding": None})
    
    print(f"Total Products: {total}")
    print(f"Missing Embedding field: {missing}")
    print(f"Null Embedding field: {null_emb}")
    
    if total > 0:
        sample = await products_col.find_one({"embedding": {"$exists": True, "$ne": None}})
        if sample:
            emb = sample["embedding"]
            print(f"Sample Embedding length: {len(emb)}")
            print(f"Sample Embedding glimpse: {emb[:5]}...")

if __name__ == "__main__":
    asyncio.run(check_embeddings())
