import asyncio
import os
import sys
from dotenv import load_dotenv
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from scripts.import_products import get_or_create_sellers, JAIPUR_SELLERS

load_dotenv()

async def test():
    sellers = await get_or_create_sellers()
    print("Sellers:", type(sellers), type(sellers[0]), sellers[0].get("email"))
    shop_info = next((s for s in JAIPUR_SELLERS if s["email"] == sellers[0]["email"]), None)
    print("Shop info:", shop_info)

asyncio.run(test())
