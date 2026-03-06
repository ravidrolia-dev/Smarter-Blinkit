"""
Comprehensive Marketplace Seed Script for Jaipur
=================================================

Fetches real products from:
- OpenFoodFacts (groceries, food items)
- OpenBeautyFacts (cosmetics, skincare)
- OpenPetFoodFacts (pet supplies)
- OpenProductsFacts (general products)

Features:
- Creates sellers with real Jaipur addresses
- Validates product images
- Generates semantic embeddings
- Assigns products to random sellers
- Comprehensive product categorization

Run with: python populate_jaipur_marketplace.py
"""

from pymongo import MongoClient
from datetime import datetime
import os
import requests
import random
import time
from dotenv import load_dotenv
import hashlib

load_dotenv()

# MongoDB Setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/smarter_blinkit")
client = MongoClient(MONGO_URI)
db = client.smarter_blinkit

def hash_password(password: str) -> str:
    """Simple password hashing for demo purposes."""
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password[:72])  # Truncate to 72 bytes for bcrypt
    except:
        # Fallback to SHA256 if bcrypt fails
        return hashlib.sha256(password.encode()).hexdigest()

# Jaipur City Center
JAIPUR_CENTER = {"lat": 26.9124, "lng": 75.7873}

# Real Jaipur Seller Locations (Markets & Popular Areas)
JAIPUR_SELLERS = [
    {
        "name": "Pink City Fresh Mart",
        "address": "MI Road, Near Panch Batti, Jaipur - 302001",
        "phone": "+91 98290 12345",
        "lat": 26.9158,
        "lng": 75.8100,
        "area": "MI Road"
    },
    {
        "name": "Johari Bazaar Grocers",
        "address": "Johari Bazaar, Old City, Jaipur - 302003",
        "phone": "+91 98290 23456",
        "lat": 26.9239,
        "lng": 75.8275,
        "area": "Johari Bazaar"
    },
    {
        "name": "Bapu Bazaar Essentials",
        "address": "Bapu Bazaar, Near Nehru Bazaar, Jaipur - 302003",
        "phone": "+91 98290 34567",
        "lat": 26.9173,
        "lng": 75.8153,
        "area": "Bapu Bazaar"
    },
    {
        "name": "Malviya Nagar Organics",
        "address": "Malviya Nagar, Near JLN Marg, Jaipur - 302017",
        "phone": "+91 98290 45678",
        "lat": 26.8510,
        "lng": 75.8050,
        "area": "Malviya Nagar"
    },
    {
        "name": "Vaishali Nagar Super Store",
        "address": "Vaishali Nagar, Near Airport, Jaipur - 302021",
        "phone": "+91 98290 56789",
        "lat": 26.9020,
        "lng": 75.7450,
        "area": "Vaishali Nagar"
    },
    {
        "name": "Mansarovar Plaza",
        "address": "Mansarovar, Sector 1, Jaipur - 302020",
        "phone": "+91 98290 67890",
        "lat": 26.8620,
        "lng": 75.7850,
        "area": "Mansarovar"
    },
    {
        "name": "C-Scheme Market Hub",
        "address": "C-Scheme, Near Ashok Marg, Jaipur - 302001",
        "phone": "+91 98290 78901",
        "lat": 26.9100,
        "lng": 75.7900,
        "area": "C-Scheme"
    },
    {
        "name": "Ajmer Road Wholesale",
        "address": "Ajmer Road, Near Sodala, Jaipur - 302006",
        "phone": "+91 98290 89012",
        "lat": 26.9300,
        "lng": 75.7500,
        "area": "Ajmer Road"
    },
    {
        "name": "Raja Park Fresh Foods",
        "address": "Raja Park, Station Road, Jaipur - 302004",
        "phone": "+91 98290 90123",
        "lat": 26.9050,
        "lng": 75.7920,
        "area": "Raja Park"
    },
    {
        "name": "Jagatpura Daily Needs",
        "address": "Jagatpura, Near Bus Stand, Jaipur - 302025",
        "phone": "+91 98290 01234",
        "lat": 26.8350,
        "lng": 75.8650,
        "area": "Jagatpura"
    }
]

# OpenFoodFacts API endpoints
OPEN_FACTS_APIS = {
    "Food": "https://world.openfoodfacts.org/api/v2/product/{barcode}.json",
    "Beauty": "https://world.openbeautyfacts.org/api/v2/product/{barcode}.json",
    "PetFood": "https://world.openpetfoodfacts.org/api/v2/product/{barcode}.json",
    "Products": "https://world.openproductsfacts.org/api/v2/product/{barcode}.json"
}

# Comprehensive barcode database across categories
PRODUCT_BARCODES = {
    "Food": [
        # Popular Indian Products
        "8901030187537",  # Parle-G Biscuits
        "8901491101004",  # Amul Butter
        "8901491101011",  # Amul Cheese
        "8901058013559",  # Britannia Marie Gold
        "8901048129895",  # Maggi Noodles
        "8901058008005",  # Britannia 50-50 Biscuits
        "8901063111417",  # Haldiram's Bhujia
        "8901396316206",  # Fortune Sunflower Oil
        "8901725161538",  # Tata Tea Gold
        "8901396188674",  # Aashirvaad Atta
        # International Food
        "5449000000996",  # Coca-Cola
        "3017620422003",  # Nutella
        "7622210824971",  # Oreo Original
        "8714100770542",  # Heinz Tomato Ketchup
        "5000159407236",  # Cadbury Dairy Milk
        "4056489087212",  # Kinder Bueno
        "8076809513487",  # Ferrero Rocher
        "7613034626844",  # KitKat
        "3017620425035",  # Nutella B-ready
        "8000500310410",  # Barilla Pasta
        # Healthy & Organic
        "737628064502",   # Nature Valley Granola Bars
        "052000337488",   # Philadelphia Cream Cheese
        "688267141553",   # Nature's Path Organic
        "4260107222217",  # Ritter Sport Chocolate
        "8001505005080",  # Lavazza Coffee
        "5000168073064",  # Twinings Tea
        "3502110004550",  # Lindt Chocolate
        "8710908501074",  # Douwe Egberts Coffee
    ],
    "Beauty": [
        # Skincare
        "3600523307371",  # L'Oréal Paris Shampoo
        "3574661111117",  # Garnier Face Wash
        "3600523315192",  # L'Oréal Elvive Shampoo
        "3600540515230",  # Maybelline Mascara
        "3600531412913",  # L'Oréal Lipstick
        "8901012153130",  # Himalaya Face Wash
        "8901012188569",  # Himalaya Nourishing Cream
        "3086123450110",  # Nivea Face Cream
        "4005900136121",  # Nivea Men Face Wash
        "3574661176109",  # Garnier Skin Naturals
        # Body Care
        "8906010070113",  # Dettol Soap
        "8901030189517",  # Lux Soap
        "8901030653391",  # Dove Soap
        "8901030668005",  # Ponds Cream
        "4902430574648",  # Pantene Shampoo
        "8901030597930",  # Sunsilk Shampoo
        # Cosmetics
        "3600530826988",  # L'Oréal Paris Makeup
        "3348901419238",  # Lancôme
        "3614272890688",  # YSL Beauty
        "3346470138124",  # Dior
    ],
    "PetFood": [
        "7613031925902",  # Purina Dog Food
        "7613035358218",  # Felix Cat Food
        "4008429131613",  # Cesar Dog Food
        "7613032431711",  # Purina ONE
        "5900951254291",  # Whiskas Cat Food
        "7613035787686",  # Purina Pro Plan
        "4008429130401",  # Pedigree
        "3065890013583",  # Royal Canin
        "7613036706063",  # Purina Cat Chow
        "5010394001137",  # Webbox Cat Treats
        "5900951020629",  # Whiskas Temptations
        "4008429061882",  # Dreamies Cat Treats
    ],
    "Products": [
        # Home & Living
        "8901030651687",  # Vim Dishwash Bar
        "8901396318606",  # Lizol Floor Cleaner
        "8901030120817",  # Surf Excel Detergent
        "8901030710681",  # Rin Detergent
        "5410076202369",  # Finish Dishwasher Tablets
        "8414271617062",  # Estrella Damm Beer
        "5011417571347",  # Walkers Crisps
        "8901396001004",  # Harpic Toilet Cleaner
        # Electronics & Accessories (general barcodes)
        "799665942747",   # Duracell Batteries
        "4902430575874",  # Panasonic Batteries
        "3574660635058",  # Gillette Razor
        "8710103789864",  # Philips LED Bulb
    ]
}

# Category to Price Range Mapping (in INR)
PRICE_RANGES = {
    "Food": (20, 500),
    "Beauty": (100, 2500),
    "PetFood": (150, 1500),
    "Products": (50, 3000)
}

# Category to Subcategory Mapping
SUBCATEGORIES = {
    "Food": ["Groceries", "Snacks", "Beverages", "Dairy", "Bakery", "Spices", "Organic"],
    "Beauty": ["Skincare", "Haircare", "Cosmetics", "Body Care", "Personal Care"],
    "PetFood": ["Dog Food", "Cat Food", "Pet Treats", "Pet Supplies"],
    "Products": ["Home Care", "Cleaning", "Electronics", "Accessories", "General"]
}

HEADERS = {
    "User-Agent": "SmarterBlinkit/1.0 (contact@smarterblinkit.com)"
}


def verify_image_url(url):
    """Verify if image URL is accessible and returns valid content."""
    if not url:
        return False
    try:
        response = requests.head(url, headers=HEADERS, timeout=5, allow_redirects=True)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            return 'image' in content_type.lower()
        
        # Some servers don't support HEAD, try GET
        response = requests.get(url, headers=HEADERS, timeout=5, stream=True, allow_redirects=True)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            return 'image' in content_type.lower()
    except Exception as e:
        print(f"      Image verification failed: {e}")
    return False


def fetch_product_from_openfacts(barcode, category):
    """Fetch product details from OpenFoodFacts APIs."""
    api_url = OPEN_FACTS_APIS[category].format(barcode=barcode)
    
    try:
        response = requests.get(api_url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return None
        
        data = response.json()
        if data.get("status") == 0:
            return None
        
        product = data.get("product", {})
        if not product:
            return None
        
        # Extract product name
        name = (
            product.get("product_name") or 
            product.get("product_name_en") or 
            product.get("generic_name") or 
            product.get("brands")
        )
        
        if not name or len(name.strip()) < 3:
            return None
        
        # Extract image URL (try multiple fields)
        image_url = (
            product.get("image_url") or
            product.get("image_front_url") or
            product.get("image_small_url") or
            product.get("image_thumb_url")
        )
        
        # Verify image before proceeding
        if not image_url or not verify_image_url(image_url):
            print(f"    ⚠️  No valid image for {name[:30]}")
            return None
        
        # Extract description
        description = (
            product.get("generic_name") or
            product.get("ingredients_text_en") or
            product.get("product_name") or
            f"High quality {category.lower()} product"
        )
        
        # Make description more meaningful
        if len(description) < 20:
            description = f"{name} - Premium {category.lower()} product with excellent quality"
        
        # Extract category/subcategory
        categories_hierarchy = product.get("categories_hierarchy", [])
        subcategory = None
        if categories_hierarchy:
            subcategory = categories_hierarchy[-1].split(":")[-1].replace("-", " ").title()
        
        if not subcategory or subcategory == "":
            subcategory = random.choice(SUBCATEGORIES[category])
        
        # Generate price
        price_low, price_high = PRICE_RANGES[category]
        price = random.randint(price_low, price_high)
        
        # Extract quantity/unit
        quantity = product.get("quantity") or "1 unit"
        
        # Extract or generate tags
        tags = []
        if product.get("brands"):
            tags.append(product["brands"].lower())
        if product.get("categories_tags"):
            tags.extend([t.replace("en:", "").replace("-", " ") for t in product["categories_tags"][:5]])
        
        # Add generic tags
        tags.extend([
            name.lower(),
            category.lower(),
            subcategory.lower(),
            "verified",
            "openfacts"
        ])
        
        tags = list(set(tags))[:10]  # Unique and limit to 10
        
        # Stock quantity
        stock = random.randint(20, 150)
        
        return {
            "name": name.strip()[:100],  # Limit name length
            "description": description.strip()[:500],  # Limit description
            "price": price,
            "category": subcategory,
            "barcode": barcode,
            "stock": stock,
            "unit": quantity,
            "image_url": image_url,
            "tags": tags,
            "rating": round(random.uniform(3.5, 5.0), 1),
            "total_sold": random.randint(10, 500),
            "source": f"OpenFacts-{category}"
        }
    
    except Exception as e:
        print(f"    ❌ Error fetching {barcode}: {str(e)[:50]}")
        return None


def create_sellers():
    """Create seller accounts in the database."""
    print("\n👥 Creating Jaipur Sellers...")
    
    seller_ids = []
    
    for seller_info in JAIPUR_SELLERS:
        email = f"seller.{seller_info['area'].lower().replace(' ', '_')}@jaipur.com"
        
        # Check if seller already exists
        existing = db.users.find_one({"email": email})
        if existing:
            print(f"  ✓ Seller exists: {seller_info['name']}")
            seller_ids.append(str(existing["_id"]))
            continue
        
        seller_doc = {
            "email": email,
            "name": seller_info["name"],
            "role": "seller",
            "phone": seller_info["phone"],
            "hashed_password": hash_password("password123"),
            "face_encoding": None,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "address": seller_info["address"],
            "area": seller_info["area"]
        }
        
        result = db.users.insert_one(seller_doc)
        seller_ids.append(str(result.inserted_id))
        print(f"  ✅ Created: {seller_info['name']} ({seller_info['area']})")
    
    return seller_ids


def fetch_all_products():
    """Fetch products from all OpenFacts APIs."""
    print("\n🔍 Fetching Products from OpenFoodFacts APIs...")
    
    all_products = []
    total_attempted = 0
    
    for category, barcodes in PRODUCT_BARCODES.items():
        print(f"\n  📦 Category: {category}")
        for barcode in barcodes:
            total_attempted += 1
            print(f"    Fetching: {barcode}...", end=" ")
            
            product = fetch_product_from_openfacts(barcode, category)
            
            if product:
                all_products.append(product)
                print(f"✓ {product['name'][:40]}")
            else:
                print("✗ Failed")
            
            time.sleep(0.5)  # Rate limiting
    
    print(f"\n  📊 Success Rate: {len(all_products)}/{total_attempted} products fetched")
    return all_products


def populate_database(products, seller_ids):
    """Populate MongoDB with products assigned to sellers."""
    print("\n💾 Populating Database...")
    
    if not products:
        print("  ❌ No products to populate!")
        return
    
    # Assign products to sellers
    products_to_insert = []
    
    for product in products:
        # Randomly assign to a seller
        seller_idx = random.randint(0, len(seller_ids) - 1)
        seller_id = seller_ids[seller_idx]
        seller_info = JAIPUR_SELLERS[seller_idx]
        
        # Add slight location jitter (within ~500 meters)
        lat_jitter = (random.random() - 0.5) * 0.008  # ~500m
        lng_jitter = (random.random() - 0.5) * 0.008
        
        product_doc = {
            **product,
            "seller_id": seller_id,
            "seller_name": seller_info["name"],
            "seller_address": seller_info["address"],
            "seller_area": seller_info["area"],
            "seller_phone": seller_info["phone"],
            "location": {
                "type": "Point",
                "coordinates": [
                    seller_info["lng"] + lng_jitter,
                    seller_info["lat"] + lat_jitter
                ]
            },
            "embedding": None,  # Will be generated by API on first search
            "created_at": datetime.utcnow()
        }
        
        products_to_insert.append(product_doc)
    
    # Insert all products
    if products_to_insert:
        result = db.products.insert_many(products_to_insert)
        print(f"  ✅ Inserted {len(result.inserted_ids)} products")
    
    # Create geospatial index
    db.products.create_index([("location", "2dsphere")])
    print("  ✅ Geospatial index created")
    
    # Create other indexes
    db.products.create_index("seller_id")
    db.products.create_index("barcode")
    db.products.create_index("category")
    print("  ✅ Additional indexes created")


def create_demo_buyer():
    """Create a demo buyer account."""
    print("\n👤 Creating Demo Buyer Account...")
    
    buyer_email = "buyer@jaipur.com"
    existing = db.users.find_one({"email": buyer_email})
    
    if existing:
        print(f"  ✓ Buyer account exists: {buyer_email}")
        return
    
    buyer_doc = {
        "email": buyer_email,
        "name": "Rajesh Kumar",
        "role": "buyer",
        "phone": "+91 98765 43210",
        "hashed_password": hash_password("buyer123"),
        "face_encoding": None,
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    
    db.users.insert_one(buyer_doc)
    print(f"  ✅ Created: {buyer_email} / buyer123")


def print_summary():
    """Print summary of populated data."""
    print("\n" + "="*60)
    print("📊 JAIPUR MARKETPLACE SUMMARY")
    print("="*60)
    
    seller_count = db.users.count_documents({"role": "seller"})
    buyer_count = db.users.count_documents({"role": "buyer"})
    product_count = db.products.count_documents({})
    
    print(f"\n👥 Sellers: {seller_count}")
    print(f"👤 Buyers: {buyer_count}")
    print(f"📦 Products: {product_count}")
    
    # Category breakdown
    print(f"\n📈 Products by Category:")
    categories = db.products.distinct("category")
    for cat in sorted(categories):
        count = db.products.count_documents({"category": cat})
        print(f"  • {cat}: {count}")
    
    # Top sellers
    print(f"\n🏪 Products per Seller:")
    for seller_info in JAIPUR_SELLERS[:5]:  # Show first 5
        seller_doc = db.users.find_one({"name": seller_info["name"]})
        if seller_doc:
            count = db.products.count_documents({"seller_id": str(seller_doc["_id"])})
            print(f"  • {seller_info['name']}: {count} products")
    
    print("\n" + "="*60)
    print("🎉 Database populated successfully!")
    print("="*60)
    
    print("\n📝 Demo Credentials:")
    print("  Buyer:  buyer@jaipur.com / buyer123")
    print("  Seller: seller.mi_road@jaipur.com / password123")
    print("  (All sellers use password123)")
    print("\n🚀 Start the backend server:")
    print("  cd backend")
    print("  uvicorn main:app --reload")
    print("\n")


def main():
    """Main execution flow."""
    print("\n" + "="*60)
    print("🛒 SMARTER BLINKIT - JAIPUR MARKETPLACE POPULATOR")
    print("="*60)
    
    try:
        # Step 1: Clear existing data (optional - ask user)
        print("\n⚠️  This will clear existing products and sellers.")
        response = input("Continue? (yes/no): ").strip().lower()
        
        if response != 'yes':
            print("❌ Operation cancelled.")
            return
        
        print("\n🗑️  Clearing existing data...")
        db.products.delete_many({})
        db.users.delete_many({"role": "seller"})
        print("  ✅ Cleared products and sellers")
        
        # Step 2: Create sellers
        seller_ids = create_sellers()
        
        # Step 3: Fetch products from OpenFacts
        products = fetch_all_products()
        
        if not products:
            print("\n❌ No products fetched. Please check your internet connection.")
            return
        
        # Step 4: Populate database
        populate_database(products, seller_ids)
        
        # Step 5: Create demo buyer
        create_demo_buyer()
        
        # Step 6: Print summary
        print_summary()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
