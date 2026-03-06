"""
Enhanced Jaipur Marketplace Populator
=====================================

Creates a comprehensive product catalog by:
1. Fetching available products from OpenFoodFacts
2. Generating realistic synthetic products with Unsplash images
3. Ensuring variety across categories
4. Assigning products to Jaipur sellers with proper location data

Run with: python enhanced_populate.py
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
    """Simple password hashing."""
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password[:72])
    except:
        return hashlib.sha256(password.encode()).hexdigest()

# Jaipur Seller Locations
JAIPUR_SELLERS = [
    {"name": "Pink City Fresh Mart", "address": "MI Road, Near Panch Batti, Jaipur - 302001", "phone": "+91 98290 12345", "lat": 26.9158, "lng": 75.8100, "area": "MI Road"},
    {"name": "Johari Bazaar Grocers", "address": "Johari Bazaar, Old City, Jaipur - 302003", "phone": "+91 98290 23456", "lat": 26.9239, "lng": 75.8275, "area": "Johari Bazaar"},
    {"name": "Bapu Bazaar Essentials", "address": "Bapu Bazaar, Near Nehru Bazaar, Jaipur - 302003", "phone": "+91 98290 34567", "lat": 26.9173, "lng": 75.8153, "area": "Bapu Bazaar"},
    {"name": "Malviya Nagar Organics", "address": "Malviya Nagar, Near JLN Marg, Jaipur - 302017", "phone": "+91 98290 45678", "lat": 26.8510, "lng": 75.8050, "area": "Malviya Nagar"},
    {"name": "Vaishali Nagar Super Store", "address": "Vaishali Nagar, Near Airport, Jaipur - 302021", "phone": "+91 98290 56789", "lat": 26.9020, "lng": 75.7450, "area": "Vaishali Nagar"},
    {"name": "Mansarovar Plaza", "address": "Mansarovar, Sector 1, Jaipur - 302020", "phone": "+91 98290 67890", "lat": 26.8620, "lng": 75.7850, "area": "Mansarovar"},
    {"name": "C-Scheme Market Hub", "address": "C-Scheme, Near Ashok Marg, Jaipur - 302001", "phone": "+91 98290 78901", "lat": 26.9100, "lng": 75.7900, "area": "C-Scheme"},
    {"name": "Ajmer Road Wholesale", "address": "Ajmer Road, Near Sodala, Jaipur - 302006", "phone": "+91 98290 89012", "lat": 26.9300, "lng": 75.7500, "area": "Ajmer Road"},
    {"name": "Raja Park Fresh Foods", "address": "Raja Park, Station Road, Jaipur - 302004", "phone": "+91 98290 90123", "lat": 26.9050, "lng": 75.7920, "area": "Raja Park"},
    {"name": "Jagatpura Daily Needs", "address": "Jagatpura, Near Bus Stand, Jaipur - 302025", "phone": "+91 98290 01234", "lat": 26.8350, "lng": 75.8650, "area": "Jagatpura"},
]

"""
Enhanced Jaipur Marketplace Populator
=====================================
Products sourced from Indian market data (Flipkart / Amazon / real market refs).
Images verified at runtime — broken links replaced with auto-generated placeholders.
Run with: python enhanced_populate.py
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
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password[:72])
    except:
        return hashlib.sha256(password.encode()).hexdigest()

# ─────────────────────────────────────────────
# Placeholder colors per category (guaranteed fallback)
# ─────────────────────────────────────────────
CATEGORY_COLORS = {
    "Groceries":     ("4CAF50", "white"),
    "Spices":        ("FF5722", "white"),
    "Beverages":     ("2196F3", "white"),
    "Dairy":         ("FFF9C4", "333333"),
    "Bakery":        ("FFCC80", "333333"),
    "Fresh Produce": ("66BB6A", "white"),
    "Snacks":        ("FF9800", "white"),
    "Instant Food":  ("F44336", "white"),
    "Electronics":   ("1565C0", "white"),
    "Medical":       ("E53935", "white"),
    "Personal Care": ("AB47BC", "white"),
    "Household":     ("546E7A", "white"),
    "Baby":          ("F48FB1", "333333"),
    "Sports":        ("00897B", "white"),
    "Stationery":    ("78909C", "white"),
    "Kitchen":       ("8D6E63", "white"),
    "Health":        ("43A047", "white"),
    "Fruits":        ("FF7043", "white"),
    "Vegetables":    ("558B2F", "white"),
    "Confectionery": ("AD1457", "white"),
}

def get_placeholder(name: str, category: str) -> str:
    bg, fg = CATEGORY_COLORS.get(category, ("607D8B", "white"))
    text = name[:22].replace(" ", "+").replace("'", "")
    return f"https://placehold.co/800x600/{bg}/{fg}?text={text}"

def verify_image(url: str) -> bool:
    if not url:
        return False
    try:
        r = requests.head(url, timeout=4, allow_redirects=True,
                          headers={"User-Agent": "Mozilla/5.0"})
        return r.status_code == 200
    except:
        return False

# ─────────────────────────────────────────────
# Jaipur Seller Locations
# ─────────────────────────────────────────────
JAIPUR_SELLERS = [
    {"name": "Pink City Fresh Mart",      "address": "MI Road, Near Panch Batti, Jaipur - 302001",         "phone": "+91 98290 12345", "lat": 26.9158, "lng": 75.8100, "area": "MI Road"},
    {"name": "Johari Bazaar Grocers",     "address": "Johari Bazaar, Old City, Jaipur - 302003",           "phone": "+91 98290 23456", "lat": 26.9239, "lng": 75.8275, "area": "Johari Bazaar"},
    {"name": "Bapu Bazaar Essentials",    "address": "Bapu Bazaar, Near Nehru Bazaar, Jaipur - 302003",    "phone": "+91 98290 34567", "lat": 26.9173, "lng": 75.8153, "area": "Bapu Bazaar"},
    {"name": "Malviya Nagar Organics",    "address": "Malviya Nagar, Near JLN Marg, Jaipur - 302017",      "phone": "+91 98290 45678", "lat": 26.8510, "lng": 75.8050, "area": "Malviya Nagar"},
    {"name": "Vaishali Nagar Super Store","address": "Vaishali Nagar, Near Airport, Jaipur - 302021",      "phone": "+91 98290 56789", "lat": 26.9020, "lng": 75.7450, "area": "Vaishali Nagar"},
    {"name": "Mansarovar Plaza",          "address": "Mansarovar, Sector 1, Jaipur - 302020",              "phone": "+91 98290 67890", "lat": 26.8620, "lng": 75.7850, "area": "Mansarovar"},
    {"name": "C-Scheme Market Hub",       "address": "C-Scheme, Near Ashok Marg, Jaipur - 302001",         "phone": "+91 98290 78901", "lat": 26.9100, "lng": 75.7900, "area": "C-Scheme"},
    {"name": "Ajmer Road Wholesale",      "address": "Ajmer Road, Near Sodala, Jaipur - 302006",           "phone": "+91 98290 89012", "lat": 26.9300, "lng": 75.7500, "area": "Ajmer Road"},
    {"name": "Raja Park Fresh Foods",     "address": "Raja Park, Station Road, Jaipur - 302004",           "phone": "+91 98290 90123", "lat": 26.9050, "lng": 75.7920, "area": "Raja Park"},
    {"name": "Jagatpura Daily Needs",     "address": "Jagatpura, Near Bus Stand, Jaipur - 302025",         "phone": "+91 98290 01234", "lat": 26.8350, "lng": 75.8650, "area": "Jagatpura"},
]

# ─────────────────────────────────────────────
# PRODUCT CATALOG  (name, description, price, category, unit, image_url, tags, barcode)
# image_url is tested at runtime; broken → auto placeholder
# ─────────────────────────────────────────────
SYNTHETIC_PRODUCTS = [

    # ═══════════════════════════════════════════
    # GROCERIES & STAPLES
    # ═══════════════════════════════════════════
    {"name": "Aashirvaad Whole Wheat Atta", "description": "100% whole wheat atta for soft rotis and parathas. Rich in fibre, no maida.", "price": 285, "category": "Groceries", "unit": "5kg",
     "image_url": "https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?w=800",
     "tags": ["atta","flour","wheat","staple"], "barcode": "8901396188674"},

    {"name": "India Gate Basmati Rice", "description": "Aged premium basmati rice — extra-long grain, aromatic fragrance, perfect for biryani.", "price": 450, "category": "Groceries", "unit": "5kg",
     "image_url": "https://images.pexels.com/photos/434295/pexels-photo-434295.jpeg?w=800",
     "tags": ["rice","basmati","biryani","staple"], "barcode": "8901063110625"},

    {"name": "Toor Dal (Arhar Dal)", "description": "Premium split pigeon peas high in protein — essential for everyday Indian dal.", "price": 145, "category": "Groceries", "unit": "1kg",
     "image_url": "https://images.pexels.com/photos/5835353/pexels-photo-5835353.jpeg?w=800",
     "tags": ["dal","protein","staple","lentils"], "barcode": "8901234567801"},

    {"name": "Tata Salt Iodised", "description": "India's most trusted iodised salt. Fine grain, free-flowing, vacuum evaporated.", "price": 22, "category": "Groceries", "unit": "1kg",
     "image_url": "https://images.pexels.com/photos/1022385/pexels-photo-1022385.jpeg?w=800",
     "tags": ["salt","iodised","cooking","staple"], "barcode": "8901058001006"},

    {"name": "Fortune Sunflower Oil", "description": "Light refined sunflower oil rich in Vitamin E. Low in saturated fats, ideal for daily cooking.", "price": 185, "category": "Groceries", "unit": "1L",
     "image_url": "https://images.pexels.com/photos/33783/olive-oil-salad-dressing-cooking-olive.jpg?w=800",
     "tags": ["oil","sunflower","healthy","cooking"], "barcode": "8901396316206"},

    {"name": "Rajdhani Chana Dal", "description": "High quality split chickpea dal. Rich taste, good source of plant protein and fibre.", "price": 110, "category": "Groceries", "unit": "1kg",
     "image_url": "https://images.pexels.com/photos/5835350/pexels-photo-5835350.jpeg?w=800",
     "tags": ["chana","dal","chickpea","lentils"], "barcode": "8906000100011"},

    {"name": "Saffola Gold Refined Oil", "description": "Blended rice bran and refined sunflower oil. Clinically proven to reduce cholesterol.", "price": 210, "category": "Groceries", "unit": "1L",
     "image_url": "https://images.pexels.com/photos/1435904/pexels-photo-1435904.jpeg?w=800",
     "tags": ["oil","heart-healthy","cooking","blended"], "barcode": "8901030673450"},

    # ═══════════════════════════════════════════
    # SPICES & CONDIMENTS
    # ═══════════════════════════════════════════
    {"name": "Everest Turmeric Powder", "description": "Pure haldi with high curcumin content. Anti-inflammatory, adds rich golden colour to curries.", "price": 68, "category": "Spices", "unit": "200g",
     "image_url": "https://images.pexels.com/photos/4198638/pexels-photo-4198638.jpeg?w=800",
     "tags": ["turmeric","haldi","spices","immunity"], "barcode": "8901786431328"},

    {"name": "MDH Garam Masala", "description": "Authentic family recipe blend of 14 premium whole spices. The heart of North Indian cooking.", "price": 75, "category": "Spices", "unit": "100g",
     "image_url": "https://images.pexels.com/photos/4198935/pexels-photo-4198935.jpeg?w=800",
     "tags": ["garam-masala","spices","cooking","mdh"], "barcode": "8901087100205"},

    {"name": "Catch Red Chilli Powder", "description": "Bright red, hot and spicy chilli powder. Adds both colour and heat to any dish.", "price": 55, "category": "Spices", "unit": "200g",
     "image_url": "https://images.pexels.com/photos/1340116/pexels-photo-1340116.jpeg?w=800",
     "tags": ["chilli","spices","hot","red-chilli"], "barcode": "8901234567802"},

    {"name": "Everest Coriander Powder", "description": "Freshly ground dhaniya powder with earthy citrusy aroma. Essential base for every curry.", "price": 48, "category": "Spices", "unit": "200g",
     "image_url": "https://images.pexels.com/photos/2802527/pexels-photo-2802527.jpeg?w=800",
     "tags": ["coriander","dhaniya","spices","powder"], "barcode": "8901786432011"},

    {"name": "MDH Kitchen King Masala", "description": "All-in-one masala for vegetable curries, paneer dishes and rice. No additives.", "price": 85, "category": "Spices", "unit": "100g",
     "image_url": "https://images.pexels.com/photos/4198936/pexels-photo-4198936.jpeg?w=800",
     "tags": ["masala","spices","kitchen-king","cooking"], "barcode": "8901087100312"},

    # ═══════════════════════════════════════════
    # BEVERAGES
    # ═══════════════════════════════════════════
    {"name": "Tata Tea Gold", "description": "Premium long-leaf and dust tea blend with unmistakable strong aroma. Perfect morning chai.", "price": 245, "category": "Beverages", "unit": "500g",
     "image_url": "https://images.pexels.com/photos/230477/pexels-photo-230477.jpeg?w=800",
     "tags": ["tea","chai","tata","morning"], "barcode": "8901725161538"},

    {"name": "Nescafe Classic Coffee", "description": "Rich, dark instant coffee made from 100% pure coffee beans. Energise your day.", "price": 295, "category": "Beverages", "unit": "200g",
     "image_url": "https://images.pexels.com/photos/1695052/pexels-photo-1695052.jpeg?w=800",
     "tags": ["coffee","nescafe","instant","beverage"], "barcode": "7613035710030"},

    {"name": "Coca-Cola Classic", "description": "The original refreshing cola. Best served ice cold at parties, meals or any moment.", "price": 40, "category": "Beverages", "unit": "750ml",
     "image_url": "https://images.pexels.com/photos/50593/coca-cola-cold-drink-soft-drink-coke-50593.jpeg?w=800",
     "tags": ["cola","soft-drink","coca-cola","refreshing"], "barcode": "5449000000996"},

    {"name": "Bisleri Mineral Water", "description": "Pure, safe and refreshing mineral water. pH balanced, packed at source.", "price": 20, "category": "Beverages", "unit": "1L",
     "image_url": "https://images.pexels.com/photos/327090/pexels-photo-327090.jpeg?w=800",
     "tags": ["water","mineral","bisleri","hydration"], "barcode": "8904022900070"},

    {"name": "Real Mixed Fruit Juice", "description": "100% mixed fruit juice, no added preservatives or artificial colour. Vitamin C enriched.", "price": 125, "category": "Beverages", "unit": "1L",
     "image_url": "https://images.pexels.com/photos/96974/pexels-photo-96974.jpeg?w=800",
     "tags": ["juice","fruit","healthy","vitamin-c"], "barcode": "8901491101905"},

    {"name": "Tropicana Orange Juice", "description": "Squeezed premium oranges with no added sugar. Rich in Vitamin C, naturally refreshing.", "price": 125, "category": "Beverages", "unit": "1L",
     "image_url": "https://images.pexels.com/photos/1435706/pexels-photo-1435706.jpeg?w=800",
     "tags": ["orange","juice","tropicana","vitamin-c"], "barcode": "9002490204020"},

    # ═══════════════════════════════════════════
    # DAIRY & BAKERY
    # ═══════════════════════════════════════════
    {"name": "Amul Butter (Salted)", "description": "Utterly Butterly Delicious! Pure pasteurised cream butter. Perfect on toast and parathas.", "price": 56, "category": "Dairy", "unit": "100g",
     "image_url": "https://images.pexels.com/photos/4110008/pexels-photo-4110008.jpeg?w=800",
     "tags": ["butter","amul","dairy","salted"], "barcode": "8901491101004"},

    {"name": "Amul Mozzarella Cheese", "description": "Creamy 100% real mozzarella that melts beautifully over pizza, pasta and garlic bread.", "price": 120, "category": "Dairy", "unit": "200g",
     "image_url": "https://images.pexels.com/photos/821365/pexels-photo-821365.jpeg?w=800",
     "tags": ["cheese","mozzarella","pizza","dairy"], "barcode": "8901491200301"},

    {"name": "Amul Toned Milk", "description": "Farm-fresh toned milk, pasteurised and homogenised. Rich in calcium and protein.", "price": 56, "category": "Dairy", "unit": "1L",
     "image_url": "https://images.pexels.com/photos/236010/pexels-photo-236010.jpeg?w=800",
     "tags": ["milk","amul","dairy","calcium"], "barcode": "8901491110051"},

    {"name": "Mother Dairy Dahi", "description": "Thick and creamy set curd with live cultures. Great for digestion, lassi and raita.", "price": 35, "category": "Dairy", "unit": "400g",
     "image_url": "https://images.pexels.com/photos/5945768/pexels-photo-5945768.jpeg?w=800",
     "tags": ["curd","dahi","probiotic","dairy"], "barcode": "8908001800011"},

    {"name": "Modern Bread (White)", "description": "Soft, fresh-baked white sandwich bread. Enriched with vitamins. Perfect for toast and sandwiches.", "price": 40, "category": "Bakery", "unit": "400g",
     "image_url": "https://images.pexels.com/photos/209206/pexels-photo-209206.jpeg?w=800",
     "tags": ["bread","bakery","sandwich","breakfast"], "barcode": "8906010535643"},

    # ═══════════════════════════════════════════
    # FRESH PRODUCE
    # ═══════════════════════════════════════════
    {"name": "Fresh Tomatoes", "description": "Farm-fresh red tomatoes. Rich in lycopene and antioxidants. Essential base for Indian cooking.", "price": 30, "category": "Vegetables", "unit": "1kg",
     "image_url": "https://images.pexels.com/photos/1327838/pexels-photo-1327838.jpeg?w=800",
     "tags": ["tomato","fresh","vegetable","farm"], "barcode": ""},

    {"name": "Fresh Onions", "description": "Premium quality red onions — the backbone of Indian curries. Strong aroma, great taste.", "price": 35, "category": "Vegetables", "unit": "1kg",
     "image_url": "https://images.pexels.com/photos/1359326/pexels-photo-1359326.jpeg?w=800",
     "tags": ["onion","vegetable","fresh","cooking"], "barcode": ""},

    {"name": "Fresh Potatoes (Aloo)", "description": "Versatile and nutritious. Great for aloo sabzi, dum aloo, fries, chaat and more.", "price": 25, "category": "Vegetables", "unit": "1kg",
     "image_url": "https://images.pexels.com/photos/144248/potatoes-vegetables-erdfrucht-bio-144248.jpeg?w=800",
     "tags": ["potato","aloo","vegetable","staple"], "barcode": ""},

    {"name": "Fresh Bananas", "description": "Ripe Robusta bananas. High in potassium and natural energy. Healthy snack or smoothie base.", "price": 50, "category": "Fruits", "unit": "1 dozen",
     "image_url": "https://images.pexels.com/photos/2872755/pexels-photo-2872755.jpeg?w=800",
     "tags": ["banana","fruit","potassium","healthy"], "barcode": ""},

    {"name": "Fresh Apples (Shimla)", "description": "Crispy Himachal Pradesh red apples. Rich in fibre and antioxidants. An apple a day!", "price": 180, "category": "Fruits", "unit": "1kg",
     "image_url": "https://images.pexels.com/photos/1510392/pexels-photo-1510392.jpeg?w=800",
     "tags": ["apple","shimla","fruit","fresh"], "barcode": ""},

    {"name": "Fresh Carrots", "description": "Bright orange carrots loaded with Vitamin A and beta-carotene. Good for eyes and immunity.", "price": 40, "category": "Vegetables", "unit": "1kg",
     "image_url": "https://images.pexels.com/photos/143133/pexels-photo-143133.jpeg?w=800",
     "tags": ["carrot","gajar","vitamin-a","vegetable"], "barcode": ""},

    # ═══════════════════════════════════════════
    # SNACKS & BRANDED FOOD
    # ═══════════════════════════════════════════
    {"name": "Parle-G Gold Biscuits", "description": "India's most loved glucose biscuits since 1939. Perfect with chai, anytime snack.", "price": 40, "category": "Snacks", "unit": "400g",
     "image_url": "https://images.pexels.com/photos/890577/pexels-photo-890577.jpeg?w=800",
     "tags": ["biscuit","parle-g","snack","tea-time"], "barcode": "8901030187537"},

    {"name": "Britannia Good Day Cashew", "description": "Rich cashew & butter cookies with a melt-in-mouth texture. Premium biscuit for tea time.", "price": 35, "category": "Snacks", "unit": "100g",
     "image_url": "https://images.pexels.com/photos/230325/pexels-photo-230325.jpeg?w=800",
     "tags": ["cookie","britannia","cashew","snack"], "barcode": "8901063108219"},

    {"name": "Lays Classic Salted", "description": "Original crispy potato chips with just the right amount of salt. Perfect movie companion.", "price": 20, "category": "Snacks", "unit": "52g",
     "image_url": "https://images.pexels.com/photos/1583884/pexels-photo-1583884.jpeg?w=800",
     "tags": ["chips","lays","potato","snack"], "barcode": "8901491110518"},

    {"name": "Haldiram's Aloo Bhujia", "description": "Famous ultra-crisp spiced potato namkeen from Haldiram's. Perfect tea-time companion.", "price": 55, "category": "Snacks", "unit": "200g",
     "image_url": "https://images.pexels.com/photos/1435904/pexels-photo-1435904.jpeg?w=800",
     "tags": ["bhujia","namkeen","haldiram","snack"], "barcode": "8901063111417"},

    {"name": "Nestle Maggi Masala Noodles", "description": "India's beloved 2-minute noodles. Tangy masala taste, quick meal any time of day.", "price": 12, "category": "Instant Food", "unit": "70g",
     "image_url": "https://images.pexels.com/photos/1907244/pexels-photo-1907244.jpeg?w=800",
     "tags": ["maggi","noodles","instant","quick-meal"], "barcode": "8901048129895"},

    {"name": "Cadbury Dairy Milk Silk", "description": "Extra smooth, velvety milk chocolate. Thicker, creamier than regular Dairy Milk.", "price": 99, "category": "Confectionery", "unit": "60g",
     "image_url": "https://images.pexels.com/photos/47013/pexels-photo-47013.jpeg?w=800",
     "tags": ["chocolate","cadbury","dairy-milk","gift"], "barcode": "8901063101159"},

    {"name": "Nestle KitKat", "description": "Crispy 4-finger wafer fingers covered in smooth chocolate. Have a break, have a KitKat!", "price": 20, "category": "Confectionery", "unit": "37g",
     "image_url": "https://images.pexels.com/photos/65882/chocolate-dark-coffee-confiserie-65882.jpeg?w=800",
     "tags": ["kitkat","chocolate","wafer","nestle"], "barcode": "8901063116481"},

    # ═══════════════════════════════════════════
    # ELECTRONICS
    # ═══════════════════════════════════════════
    {"name": "Samsung Galaxy A55 5G", "description": "6.6\" Super AMOLED, 50MP OIS camera, 5000mAh battery, 8GB RAM. 5G ready smartphone.", "price": 34999, "category": "Electronics", "unit": "1 piece",
     "image_url": "https://images.pexels.com/photos/788946/pexels-photo-788946.jpeg?w=800",
     "tags": ["smartphone","samsung","5g","android"], "barcode": "8806095264790"},

    {"name": "Redmi Note 13 Pro", "description": "200MP camera, 6.67\" AMOLED, 5100mAh, 67W turbo charge. Best mid-range performer.", "price": 22999, "category": "Electronics", "unit": "1 piece",
     "image_url": "https://images.pexels.com/photos/47261/pexels-photo-47261.jpeg?w=800",
     "tags": ["smartphone","redmi","xiaomi","camera"], "barcode": "6934177793684"},

    {"name": "HP Laptop 15 (Intel i5)", "description": "15.6\" FHD display, 12th Gen Intel i5, 8GB RAM, 512GB SSD, Windows 11. Reliable everyday laptop.", "price": 52990, "category": "Electronics", "unit": "1 piece",
     "image_url": "https://images.pexels.com/photos/18105/pexels-photo.jpg?w=800",
     "tags": ["laptop","hp","windows","intel-i5"], "barcode": "0197497267790"},

    {"name": "boAt Rockerz 450 Headphones", "description": "40mm drivers, 15HR playback, foldable on-ear Bluetooth headphones with mic. Deep bass.", "price": 1299, "category": "Electronics", "unit": "1 piece",
     "image_url": "https://images.pexels.com/photos/3394650/pexels-photo-3394650.jpeg?w=800",
     "tags": ["headphones","boat","bluetooth","bass"], "barcode": "8906054405100"},

    {"name": "Sony WH-1000XM5 ANC", "description": "Industry-leading noise cancellation, 30HR battery, LDAC hi-res audio, multipoint connection.", "price": 29990, "category": "Electronics", "unit": "1 piece",
     "image_url": "https://images.pexels.com/photos/3587478/pexels-photo-3587478.jpeg?w=800",
     "tags": ["headphones","sony","noise-cancelling","premium"], "barcode": "4548736132559"},

    {"name": "JBL Go 3 Bluetooth Speaker", "description": "Waterproof IPX67 portable speaker. Loud sound with bold bass, 5HR playtime.", "price": 2999, "category": "Electronics", "unit": "1 piece",
     "image_url": "https://images.pexels.com/photos/1034425/pexels-photo-1034425.jpeg?w=800",
     "tags": ["speaker","jbl","bluetooth","portable"], "barcode": "6925281984914"},

    {"name": "Mi Power Bank 20000mAh", "description": "20000mAh capacity, 22.5W fast charging, dual USB-A + USB-C ports, LED indicator.", "price": 1799, "category": "Electronics", "unit": "1 piece",
     "image_url": "https://images.pexels.com/photos/4526404/pexels-photo-4526404.jpeg?w=800",
     "tags": ["powerbank","mi","charger","portable"], "barcode": "6941059641049"},

    {"name": "Samsung 43\" Crystal 4K TV", "description": "4K UHD, Crystal Processor, HDR, Tizen Smart TV, 3 HDMI, 20W speakers. Vivid picture quality.", "price": 34990, "category": "Electronics", "unit": "1 piece",
     "image_url": "https://images.pexels.com/photos/6976094/pexels-photo-6976094.jpeg?w=800",
     "tags": ["tv","samsung","4k","smart-tv"], "barcode": "8806094905915"},

    {"name": "Apple AirPods (3rd Gen)", "description": "Spatial audio, force sensor controls, MagSafe charging case, 30HR total battery life.", "price": 19900, "category": "Electronics", "unit": "1 piece",
     "image_url": "https://images.pexels.com/photos/3780681/pexels-photo-3780681.jpeg?w=800",
     "tags": ["airpods","apple","tws","earbuds"], "barcode": "0194252930748"},

    {"name": "Canon EOS 1500D DSLR", "description": "24.1MP APS-C sensor, 9-point AF, Full HD video, built-in Wi-Fi, EF-S 18-55mm kit lens.", "price": 34995, "category": "Electronics", "unit": "1 piece",
     "image_url": "https://images.pexels.com/photos/90946/pexels-photo-90946.jpeg?w=800",
     "tags": ["camera","dslr","canon","photography"], "barcode": "4549292113891"},

    # ═══════════════════════════════════════════
    # MEDICAL & HEALTHCARE
    # ═══════════════════════════════════════════
    {"name": "Dettol Antiseptic Liquid", "description": "The original trusted antiseptic. Kills 99.9% of germs. For cuts, wounds and skin hygiene.", "price": 95, "category": "Medical", "unit": "500ml",
     "image_url": "https://images.pexels.com/photos/3683074/pexels-photo-3683074.jpeg?w=800",
     "tags": ["antiseptic","dettol","wound-care","hygiene"], "barcode": "8906010070021"},

    {"name": "Vicks VapoRub", "description": "Fast relief from blocked nose, cough and body aches. Classic mentho-camphor rub.", "price": 85, "category": "Medical", "unit": "50g",
     "image_url": "https://images.pexels.com/photos/3683015/pexels-photo-3683015.jpeg?w=800",
     "tags": ["vicks","cold","cough","vapour"], "barcode": "8906030300081"},

    {"name": "Crocin Advance Paracetamol", "description": "Fast-acting paracetamol 500mg tablets. Relieves fever, headache and mild pain.", "price": 32, "category": "Medical", "unit": "15 tablets",
     "image_url": "https://images.pexels.com/photos/208518/pexels-photo-208518.jpeg?w=800",
     "tags": ["paracetamol","painkiller","fever","tablet"], "barcode": "8901080006013"},

    {"name": "Dabur Honey", "description": "100% pure with no added sugar. Antibacterial, antioxidant properties. Natural energy booster.", "price": 285, "category": "Health", "unit": "500g",
     "image_url": "https://images.pexels.com/photos/87425/honey-sweet-syrup-organic-87425.jpeg?w=800",
     "tags": ["honey","dabur","immunity","natural"], "barcode": "8901207001048"},

    {"name": "Revital H Multivitamin", "description": "Daily supplement with 30 vitamins, minerals and ginseng. Boosts energy and vitality.", "price": 365, "category": "Medical", "unit": "30 capsules",
     "image_url": "https://images.pexels.com/photos/3683053/pexels-photo-3683053.jpeg?w=800",
     "tags": ["multivitamin","supplement","health","energy"], "barcode": "8901674100114"},

    {"name": "Volini Relispray (Pain Relief)", "description": "Instant spray-on relief for muscle pain, back pain, sprains and joint ache.", "price": 175, "category": "Medical", "unit": "55g",
     "image_url": "https://images.pexels.com/photos/5699516/pexels-photo-5699516.jpeg?w=800",
     "tags": ["pain-relief","spray","muscle","volini"], "barcode": "8901546000115"},

    {"name": "Glucon-D Instant Energy", "description": "Glucose powder with added calcium and Vitamin D. Replenishes energy within minutes.", "price": 99, "category": "Health", "unit": "400g",
     "image_url": "https://images.pexels.com/photos/3768916/pexels-photo-3768916.jpeg?w=800",
     "tags": ["glucose","energy","summer","electrolyte"], "barcode": "8901719100087"},

    {"name": "Betadine Antiseptic Solution", "description": "Povidone-iodine 5% for wound cleansing, pre-surgical prep and minor infections.", "price": 72, "category": "Medical", "unit": "100ml",
     "image_url": "https://images.pexels.com/photos/4047134/pexels-photo-4047134.jpeg?w=800",
     "tags": ["betadine","iodine","wound-care","antiseptic"], "barcode": "8901314300144"},

    # ═══════════════════════════════════════════
    # PERSONAL CARE & BEAUTY
    # ═══════════════════════════════════════════
    {"name": "Himalaya Neem Face Wash", "description": "Herbal face wash with neem and turmeric. Deep cleanses pores, fights acne. Dermatologist tested.", "price": 145, "category": "Personal Care", "unit": "150ml",
     "image_url": "https://images.pexels.com/photos/4041392/pexels-photo-4041392.jpeg?w=800",
     "tags": ["facewash","neem","skincare","himalaya"], "barcode": "8901012153130"},

    {"name": "Dettol Original Soap", "description": "Germ-protection soap trusted worldwide. Antibacterial formula protects for up to 12 hours.", "price": 40, "category": "Personal Care", "unit": "125g",
     "image_url": "https://images.pexels.com/photos/3735657/pexels-photo-3735657.jpeg?w=800",
     "tags": ["soap","dettol","antibacterial","hygiene"], "barcode": "8906010070113"},

    {"name": "Dove Moisturising Soap", "description": "Beauty bar with 1/4 moisturising cream. Leaves skin soft, smooth and nourished.", "price": 65, "category": "Personal Care", "unit": "125g",
     "image_url": "https://images.pexels.com/photos/4202391/pexels-photo-4202391.jpeg?w=800",
     "tags": ["soap","dove","moisturising","beauty"], "barcode": "8901030653391"},

    {"name": "Pantene Shampoo (Damage Repair)", "description": "Pro-V formula repairs damage in just 3 washes. Strong, shiny hair from root to tip.", "price": 299, "category": "Personal Care", "unit": "340ml",
     "image_url": "https://images.pexels.com/photos/4465121/pexels-photo-4465121.jpeg?w=800",
     "tags": ["shampoo","pantene","hair-care","repair"], "barcode": "8001841205793"},

    {"name": "Colgate MaxFresh Toothpaste", "description": "Cooling crystals and mint freshness. Whitening, anti-cavity and 12-hour fresh breath.", "price": 85, "category": "Personal Care", "unit": "150g",
     "image_url": "https://images.pexels.com/photos/3786126/pexels-photo-3786126.jpeg?w=800",
     "tags": ["toothpaste","colgate","whitening","oral-care"], "barcode": "8718951223295"},

    {"name": "Parachute Coconut Oil", "description": "100% pure coconut oil for hair and skin. Reduces frizz, adds shine, promotes growth.", "price": 165, "category": "Personal Care", "unit": "500ml",
     "image_url": "https://images.pexels.com/photos/2733659/pexels-photo-2733659.jpeg?w=800",
     "tags": ["coconut-oil","parachute","hair-oil","natural"], "barcode": "8901248101059"},

    {"name": "Nivea Soft Light Moisturiser", "description": "Light, non-greasy body lotion with Jojoba oil and Vitamin E. Instant moisture for all skin.", "price": 225, "category": "Personal Care", "unit": "200ml",
     "image_url": "https://images.pexels.com/photos/3685538/pexels-photo-3685538.jpeg?w=800",
     "tags": ["moisturiser","nivea","skin-care","lotion"], "barcode": "4005900028563"},

    {"name": "Gillette Mach3 Razor", "description": "3-blade shaving technology for a smooth, close shave. Aloe vera lubricating strip.", "price": 199, "category": "Personal Care", "unit": "1 piece",
     "image_url": "https://images.pexels.com/photos/3621234/pexels-photo-3621234.jpeg?w=800",
     "tags": ["razor","gillette","shaving","grooming"], "barcode": "7702018898787"},

    # ═══════════════════════════════════════════
    # HOUSEHOLD & CLEANING
    # ═══════════════════════════════════════════
    {"name": "Vim Dishwash Bar", "description": "Removes tough grease and baked-on food. Lemon fresh. Cleans 3x more dishes vs liquid.", "price": 10, "category": "Household", "unit": "200g",
     "image_url": "https://images.pexels.com/photos/4099471/pexels-photo-4099471.jpeg?w=800",
     "tags": ["dishwash","cleaning","vim","household"], "barcode": "8901030651687"},

    {"name": "Surf Excel Easy Wash", "description": "Tough stain remover, gentle on clothes and hands. Works in just 2 mugs of water.", "price": 345, "category": "Household", "unit": "2kg",
     "image_url": "https://images.pexels.com/photos/4109365/pexels-photo-4109365.jpeg?w=800",
     "tags": ["detergent","surf-excel","washing","stain"], "barcode": "8901030120817"},

    {"name": "Harpic Power Plus", "description": "Kills 99.9% germs including E-coli. Cleans and deodorises under the rim. 10x better hygiene.", "price": 95, "category": "Household", "unit": "500ml",
     "image_url": "https://images.pexels.com/photos/4108715/pexels-photo-4108715.jpeg?w=800",
     "tags": ["toilet-cleaner","harpic","hygiene","disinfectant"], "barcode": "8901396001004"},

    {"name": "Colin Glass & Surface Cleaner", "description": "Streak-free sparkling clean for glass, mirrors and stainless steel. Ready to use spray.", "price": 75, "category": "Household", "unit": "500ml",
     "image_url": "https://images.pexels.com/photos/4099238/pexels-photo-4099238.jpeg?w=800",
     "tags": ["glass-cleaner","colin","streak-free","household"], "barcode": "8901030607097"},

    {"name": "Good Knight Mosquito Coil", "description": "12-hour protection against mosquitoes. Effective outdoors and in well-ventilated areas.", "price": 25, "category": "Household", "unit": "10 coils",
     "image_url": "https://images.pexels.com/photos/3735221/pexels-photo-3735221.jpeg?w=800",
     "tags": ["mosquito","coil","protection","goodknight"], "barcode": "8901396029009"},

    {"name": "Lizol Disinfectant Floor Cleaner", "description": "Kills 99.9% germs on floors. Pine fragrance, tested against COVID-19 virus.", "price": 115, "category": "Household", "unit": "500ml",
     "image_url": "https://images.pexels.com/photos/4239011/pexels-photo-4239011.jpeg?w=800",
     "tags": ["floor-cleaner","lizol","disinfectant","hygiene"], "barcode": "8901396029122"},

    # ═══════════════════════════════════════════
    # BABY & KIDS
    # ═══════════════════════════════════════════
    {"name": "Pampers Baby Dry Diapers (M)", "description": "Up to 12hr overnight dryness with 3 absorb channels. Soft waistband, no leaks.", "price": 699, "category": "Baby", "unit": "50 count",
     "image_url": "https://images.pexels.com/photos/35537/child-children-girl-happy.jpg?w=800",
     "tags": ["diapers","pampers","baby","newborn"], "barcode": "4987176241672"},

    {"name": "Johnson's Baby Powder", "description": "Gentle talc-free formula with soothing aloe. Keeps baby soft, fresh and comfortable.", "price": 159, "category": "Baby", "unit": "200g",
     "image_url": "https://images.pexels.com/photos/1648387/pexels-photo-1648387.jpeg?w=800",
     "tags": ["baby-powder","johnson","gentle","talc-free"], "barcode": "8901506001224"},

    {"name": "Nestle Cerelac Wheat & Honey", "description": "Stage-2 infant cereal fortified with 18 nutrients including iron, zinc and vitamin D.", "price": 255, "category": "Baby", "unit": "300g",
     "image_url": "https://images.pexels.com/photos/1120349/pexels-photo-1120349.jpeg?w=800",
     "tags": ["cerelac","baby-food","nestle","infant"], "barcode": "8901571002063"},

    {"name": "Fisher-Price Rattle Toy Set", "description": "BPA-free sensory rattles for 3-month+ babies. Develops grip, colours and sound recognition.", "price": 449, "category": "Baby", "unit": "3 pieces",
     "image_url": "https://images.pexels.com/photos/36029/artem-bali-97704.jpg?w=800",
     "tags": ["baby-toy","rattle","fisher-price","sensory"], "barcode": "0887961185782"},

    # ═══════════════════════════════════════════
    # SPORTS & FITNESS
    # ═══════════════════════════════════════════
    {"name": "Yoga Mat (6mm Anti-Slip)", "description": "Extra-thick 6mm TPE foam mat. Non-slip surface, carry strap included. 183×61cm.", "price": 799, "category": "Sports", "unit": "1 piece",
     "image_url": "https://images.pexels.com/photos/4662438/pexels-photo-4662438.jpeg?w=800",
     "tags": ["yoga","mat","fitness","exercise"], "barcode": ""},

    {"name": "Optimum Nutrition Whey Protein", "description": "24g protein per serving, 5.5g BCAAs, Gold Standard 100% Whey. Chocolate flavour.", "price": 3499, "category": "Sports", "unit": "1kg",
     "image_url": "https://images.pexels.com/photos/3766213/pexels-photo-3766213.jpeg?w=800",
     "tags": ["protein","whey","supplement","fitness"], "barcode": "0748927023855"},

    {"name": "Cosco Iron Dumbbell Set", "description": "Pair of 5kg cast iron dumbbells with chrome handles. Rubber end caps, no-roll design.", "price": 1299, "category": "Sports", "unit": "2×5kg",
     "image_url": "https://images.pexels.com/photos/416778/pexels-photo-416778.jpeg?w=800",
     "tags": ["dumbbell","weight","gym","fitness"], "barcode": "8906005420031"},

    {"name": "Nivia Racer Sports Water Bottle", "description": "BPA-free tritan bottle with leak-proof flip lid and carry loop. Dishwasher safe.", "price": 349, "category": "Sports", "unit": "750ml",
     "image_url": "https://images.pexels.com/photos/863988/pexels-photo-863988.jpeg?w=800",
     "tags": ["water-bottle","sports","gym","bpa-free"], "barcode": "8906021950028"},

    # ═══════════════════════════════════════════
    # STATIONERY & OFFICE
    # ═══════════════════════════════════════════
    {"name": "Classmate Single Line Notebook", "description": "200 pages thick writing paper. Hardbound cover, easy-tear micro-perforated pages.", "price": 65, "category": "Stationery", "unit": "200 pages",
     "image_url": "https://images.pexels.com/photos/733857/pexels-photo-733857.jpeg?w=800",
     "tags": ["notebook","classmate","stationery","school"], "barcode": "8906011840038"},

    {"name": "Reynolds Trimax Ballpen (Blue)", "description": "Super-smooth ball point pen with 1000m writing capacity. Ergonomic rubber grip.", "price": 50, "category": "Stationery", "unit": "10 pens",
     "image_url": "https://images.pexels.com/photos/159478/pens_colored-159478.jpeg?w=800",
     "tags": ["pen","ballpen","reynolds","writing"], "barcode": "8901508000163"},

    {"name": "Kokuyo Camlin Oil Pastels", "description": "48 vibrant oil pastels for school and art projects. Blendable, rich pigments.", "price": 149, "category": "Stationery", "unit": "48 colours",
     "image_url": "https://images.pexels.com/photos/1148496/pexels-photo-1148496.jpeg?w=800",
     "tags": ["pastel","art","camlin","school"], "barcode": "8901710135031"},

    {"name": "HP A4 Printer Paper", "description": "80gsm bright white multipurpose paper. Compatible with inkjet and laser printers.", "price": 499, "category": "Stationery", "unit": "500 sheets",
     "image_url": "https://images.pexels.com/photos/1043514/pexels-photo-1043514.jpeg?w=800",
     "tags": ["paper","a4","printer","hp"], "barcode": "0882780967538"},

    # ═══════════════════════════════════════════
    # KITCHEN & HOME APPLIANCES
    # ═══════════════════════════════════════════
    {"name": "Prestige Pressure Cooker 3L", "description": "3L aluminium pressure cooker with gasket release system for safe venting. ISI mark.", "price": 1195, "category": "Kitchen", "unit": "3 Litres",
     "image_url": "https://images.pexels.com/photos/1440727/pexels-photo-1440727.jpeg?w=800",
     "tags": ["pressure-cooker","prestige","kitchen","cooking"], "barcode": "8906006020039"},

    {"name": "Bajaj Rex Mixer Grinder 500W", "description": "500W motor, 3 stainless steel jars (1.5L, 0.8L, 0.4L), overload protection.", "price": 2495, "category": "Kitchen", "unit": "1 piece",
     "image_url": "https://images.pexels.com/photos/4397800/pexels-photo-4397800.jpeg?w=800",
     "tags": ["mixer","grinder","bajaj","kitchen"], "barcode": "8906021990024"},

    {"name": "Milton Thermosteel Flask 500ml", "description": "24hr hot / 24hr cold. Double-wall vacuum insulated stainless steel. Leak-proof.", "price": 649, "category": "Kitchen", "unit": "500ml",
     "image_url": "https://images.pexels.com/photos/4551832/pexels-photo-4551832.jpeg?w=800",
     "tags": ["flask","thermos","milton","insulated"], "barcode": "8906004720053"},

    {"name": "Cello Opalware Dinner Set", "description": "19-piece bone-china strong opalware. Microwave, dishwasher and freezer safe.", "price": 1299, "category": "Kitchen", "unit": "19 pieces",
     "image_url": "https://images.pexels.com/photos/3184183/pexels-photo-3184183.jpeg?w=800",
     "tags": ["dinnerware","cello","dinner-set","opalware"], "barcode": "8906006090108"},
]


def create_sellers():
    """Create seller accounts."""
    print("\n👥 Creating Jaipur Sellers...")
    seller_ids = []
    
    for seller_info in JAIPUR_SELLERS:
        email = f"seller.{seller_info['area'].lower().replace(' ', '_')}@jaipur.com"
        
        existing = db.users.find_one({"email": email})
        if existing:
            print(f"  ✓ {seller_info['name']}")
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
            "created_at": datetime.now(),
            "address": seller_info["address"],
            "area": seller_info["area"]
        }
        
        result = db.users.insert_one(seller_doc)
        seller_ids.append(str(result.inserted_id))
        print(f"  ✅ {seller_info['name']}")
    
    return seller_ids

def populate_products(seller_ids):
    """Populate database with products."""
    print(f"\n📦 Adding {len(SYNTHETIC_PRODUCTS)} Products...")
    
    products_to_insert = []
    
    print("  🔍 Verifying image URLs (may take a moment)...")
    for i, product in enumerate(SYNTHETIC_PRODUCTS):
        # Assign to seller (distribute evenly)
        seller_idx = i % len(seller_ids)
        seller_id = seller_ids[seller_idx]
        seller_info = JAIPUR_SELLERS[seller_idx]
        
        # Verify image URL — fallback to colored placeholder if broken
        img_url = product.get("image_url", "")
        if not verify_image(img_url):
            img_url = get_placeholder(product["name"], product["category"])
            print(f"    ⚠ [{i+1}/{len(SYNTHETIC_PRODUCTS)}] Placeholder used for: {product['name']}")
        
        # Location with slight jitter
        lat_jitter = (random.random() - 0.5) * 0.005
        lng_jitter = (random.random() - 0.5) * 0.005
        
        product_doc = {
            **product,
            "image_url": img_url,
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
            "stock": random.randint(30, 200),
            "rating": round(random.uniform(3.8, 5.0), 1),
            "total_sold": random.randint(50, 800),
            "embedding": None,
            "created_at": datetime.now()
        }
        
        products_to_insert.append(product_doc)
    
    # Insert all
    result = db.products.insert_many(products_to_insert)
    print(f"  ✅ Inserted {len(result.inserted_ids)} products")
    
    # Create indexes
    db.products.create_index([("location", "2dsphere")])
    db.products.create_index("seller_id")
    db.products.create_index("barcode")
    db.products.create_index("category")
    db.products.create_index("tags")
    print("  ✅ Indexes created")

def create_demo_buyer():
    """Create demo buyer."""
    print("\n👤 Creating Demo Buyer...")
    
    buyer_email = "buyer@jaipur.com"
    if db.users.find_one({"email": buyer_email}):
        print(f"  ✓ Buyer exists")
        return
    
    buyer_doc = {
        "email": buyer_email,
        "name": "Rajesh Kumar",
        "role": "buyer",
        "phone": "+91 98765 43210",
        "hashed_password": hash_password("buyer123"),
        "face_encoding": None,
        "is_active": True,
        "created_at": datetime.now()
    }
    
    db.users.insert_one(buyer_doc)
    print(f"  ✅ Created: {buyer_email} / buyer123")

def print_summary():
    """Print summary."""
    print("\n" + "="*70)
    print("📊 JAIPUR MARKETPLACE - COMPREHENSIVE SUMMARY")
    print("="*70)
    
    seller_count = db.users.count_documents({"role": "seller"})
    buyer_count = db.users.count_documents({"role": "buyer"})
    product_count = db.products.count_documents({})
    
    print(f"\n👥 Sellers: {seller_count}")
    print(f"👤 Buyers: {buyer_count}")
    print(f"📦 Total Products: {product_count}")
    
    print(f"\n📈 Products by Category:")
    categories = db.products.distinct("category")
    for cat in sorted(categories):
        count = db.products.count_documents({"category": cat})
        print(f"  • {cat}: {count} products")
    
    print(f"\n🏪 Distribution across Sellers:")
    for seller_info in JAIPUR_SELLERS:
        seller_doc = db.users.find_one({"name": seller_info["name"]})
        if seller_doc:
            count = db.products.count_documents({"seller_id": str(seller_doc["_id"])})
            print(f"  • {seller_info['name']}: {count} products")
    
    print("\n" + "="*70)
    print("🎉 DATABASE FULLY POPULATED!")
    print("="*70)
    
    print("\n📝 Login Credentials:")
    print("  🛒 Buyer:   buyer@jaipur.com / buyer123")
    print("  🏪 Sellers: seller.[area]@jaipur.com / password123")
    print("\n  Examples:")
    print("    • seller.mi_road@jaipur.com / password123")
    print("    • seller.johari_bazaar@jaipur.com / password123")
    
    print("\n🚀 Next Steps:")
    print("  1. Start backend:  cd backend && uvicorn main:app --reload")
    print("  2. Visit API docs: http://localhost:8000/docs")
    print("  3. Start frontend: cd frontend && npm run dev")
    print("  4. Browse app:     http://localhost:3000")
    print("")

def main():
    """Main execution."""
    print("\n" + "="*70)
    print("🛒 ENHANCED JAIPUR MARKETPLACE POPULATOR")
    print("="*70)
    print("\nThis will:", end="")
    print(f"\n  • Clear existing products and sellers")
    print(f"  • Create {len(JAIPUR_SELLERS)} sellers across Jaipur")
    print(f"  • Add {len(SYNTHETIC_PRODUCTS)} realistic products")
    print(f"  • Assign products to sellers evenly")
    
    response = input("\nContinue? (yes/no): ").strip().lower()
    if response != 'yes':
        print("❌ Cancelled")
        return
    
    try:
        print("\n🗑️  Clearing existing data...")
        db.products.delete_many({})
        db.users.delete_many({"role": "seller"})
        print("  ✅ Cleared")
        
        seller_ids = create_sellers()
        populate_products(seller_ids)
        create_demo_buyer()
        print_summary()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
