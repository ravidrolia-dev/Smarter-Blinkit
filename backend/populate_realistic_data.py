import requests
import time
import random

BASE_URL = "http://localhost:8000"

# Open Facts API Templates
APIS = {
    "Groceries": "https://world.openfoodfacts.org/api/v2/product/{barcode}.json",
    "Beauty": "https://world.openbeautyfacts.org/api/v2/product/{barcode}.json",
    "Pet Food": "https://world.openpetfoodfacts.org/api/v2/product/{barcode}.json",
    "Products": "https://world.openproductsfacts.org/api/v2/product/{barcode}.json"
}

# Jaipur Center Coordinates
JAIPUR_LAT = 26.9124
JAIPUR_LNG = 75.7873

# Random Seller Names & Locations
SELLER_REGISTRY = [
    {"name": "Pink City Electronics", "address": "MI Road, Jaipur", "lat": 26.915, "lng": 75.810},
    {"name": "Johari Bazaar Gourmet", "address": "Johari Bazaar, Jaipur", "lat": 26.923, "lng": 75.827},
    {"name": "Bapu Bazaar Textiles & More", "address": "Bapu Bazaar, Jaipur", "lat": 26.917, "lng": 75.815},
    {"name": "Jaipur Tech Hub", "address": "Malviya Nagar, Jaipur", "lat": 26.850, "lng": 75.800},
    {"name": "Hawa Mahal Crafts", "address": "Sireh Deori, Jaipur", "lat": 26.924, "lng": 75.825},
    {"name": "Amer Road Organics", "address": "Amer Road, Jaipur", "lat": 26.950, "lng": 75.840},
    {"name": "Bapu Bazaar Essentials", "address": "Bapu Bazaar, Jaipur", "lat": 26.918, "lng": 75.816},
    {"name": "MI Road Signature", "address": "MI Road, Jaipur", "lat": 26.916, "lng": 75.811}
]

# Barcode Sets
BARCODES = {
    "Groceries": ["5449000000996", "3017620422003", "8901058000040", "7622210824971", "8901491101830"],
    "Beauty": ["3600522822554", "8410148002011", "3052100412654", "3145891255300", "3600523823611"],
    "Pet Food": ["7613032431711", "4008429131613", "3065890013583", "7613035787686", "4008429130401"],
    "Products": ["8414271617062", "5410076202369", "5011417571347", "8901396001004"]
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def verify_image(url):
    """Verify if image URL returns 200."""
    try:
        r = requests.head(url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return True
        # Some servers block HEAD, try GET with stream
        r = requests.get(url, headers=HEADERS, timeout=5, stream=True)
        return r.status_code == 200
    except:
        return False

def fetch_open_facts_data(barcode, category_key):
    api_url = APIS[category_key].format(barcode=barcode)
    print(f"🔍 Fetching {category_key} info for {barcode}...")
    try:
        r = requests.get(api_url, timeout=10)
        if r.status_code == 200:
            p = r.json().get("product", {})
            if not p: return None
            
            name = p.get("product_name") or p.get("product_name_en") or "Unknown Product"
            img = p.get("image_url") or p.get("image_front_url")
            
            # ATLEAST VALIDATE IMAGE BEFORE ADDING
            if not img or not verify_image(img):
                print(f"  ⚠️ Skipping {barcode}: Broken or missing image link.")
                return None
            
            # Simple pricing logic based on category
            price_map = {"Groceries": [45, 199], "Beauty": [299, 2499], "Pet Food": [199, 1499], "Products": [99, 4999]}
            low, high = price_map[category_key]
            
            return {
                "name": name,
                "description": p.get("generic_name") or f"High quality {category_key} item: {name}",
                "price": random.randint(low, high),
                "category": category_key,
                "unit": p.get("quantity") or "1 unit",
                "barcode": barcode,
                "image_url": img,
                "tags": [name.lower(), category_key.lower(), "openfacts"],
                "stock": random.randint(10, 50)
            }
    except Exception as e:
        print(f"  ❌ Error fetching {barcode}: {e}")
    return None

def seed():
    print("🚀 Starting Verified Open Facts Seeding in Jaipur...")
    
    # 1. Scrape and Verify Data
    all_verified_products = []
    for cat, codes in BARCODES.items():
        for b in codes:
            p = fetch_open_facts_data(b, cat)
            if p:
                all_verified_products.append(p)
                print(f"  ✅ Verified: {p['name']}")
    
    if not all_verified_products:
        print("❌ No verified products found. Exiting.")
        return

    # 2. Assign to Jaipur Sellers
    for seller in SELLER_REGISTRY:
        email = f"seller_{seller['name'].lower().replace(' ', '_')}@jaipur.com"
        password = "password123"
        
        # Ensure seller exists
        requests.post(f"{BASE_URL}/auth/register", json={
            "email": email, "name": seller["name"], "password": password, "role": "seller", "phone": f"98290{random.randint(10000, 99999)}"
        }, timeout=5)
        
        # Retry login a few times in case backend is warming up
        token = None
        for _ in range(5):
            try:
                login = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password}, timeout=5)
                if login.status_code == 200:
                    token = login.json()["access_token"]
                    break
            except: pass
            time.sleep(1)
            
        if not token:
            print(f"  ❌ Could not connect to backend for {email}")
            continue
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # Jitter location
        lat = seller["lat"] + (random.random() - 0.5) * 0.01
        lng = seller["lng"] + (random.random() - 0.5) * 0.01
        
        # Pick 3-5 random products
        my_prods = random.sample(all_verified_products, min(len(all_verified_products), random.randint(3, 5)))
        
        print(f"🏢 Seller: {seller['name']} ({seller['address']})")
        for p in my_prods:
            p_copy = p.copy()
            p_copy["lat"] = lat
            p_copy["lng"] = lng
            p_copy["address"] = seller["address"]
            p_copy["mrp"] = p_copy["price"] + random.randint(10, 100)
            
            try:
                res = requests.post(f"{BASE_URL}/products", json=p_copy, headers=headers, timeout=10)
                if res.status_code == 201:
                    print(f"  🎁 Added: {p_copy['name']}")
            except Exception as e:
                print(f"  ⚠️ Failed to add {p_copy['name']}: {e}")

    print("\n✨ Jaipur Marketplace Re-Populated with VERIFIED Open Facts Data!")

if __name__ == "__main__":
    seed()
