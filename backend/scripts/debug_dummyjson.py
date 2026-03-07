import asyncio
import os
import sys
import requests
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_products_collection

load_dotenv()

async def investigate_dummyjson():
    print("--- Fetching all DummyJSON Products ---")
    try:
        r = requests.get("https://dummyjson.com/products?limit=200", timeout=10)
        if r.status_code == 200:
            data = r.json().get("products", [])
            print(f"Fetched {len(data)} products.")
            for p in data[:5]:
                print(f"Title: {p.get('title')}, Thumbnail: {p.get('thumbnail')}, Category: {p.get('category')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(investigate_dummyjson())
