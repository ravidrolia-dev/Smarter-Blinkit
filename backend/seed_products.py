import requests
import json
import random

BASE_URL = "http://localhost:8000"

def seed():
    print("🛒 Starting Data Seeding Process...")
    
    # 1. Register or Login Seller
    seller_data = {
        "email": "demo_seller@blinkit.com",
        "name": "BlinkIt Demo Store",
        "password": "password123",
        "role": "seller",
        "phone": "9998887776"
    }
    
    # Attempt to register
    req = requests.post(f"{BASE_URL}/auth/register", json=seller_data)
    if req.status_code == 201:
        print("✅ Registered new demo seller")
    
    # Login to get token
    login_req = requests.post(f"{BASE_URL}/auth/login", json={"email": "demo_seller@blinkit.com", "password": "password123"})
    if login_req.status_code != 200:
        print("❌ Login failed:", login_req.json())
        return
        
    token = login_req.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("🔑 Authenticated Demo Seller")

    # 2. Define diverse products
    products = [
        {
            "name": "Farm Fresh Bananas",
            "description": "Sweet, ripe, and delicious bananas direct from local farms.",
            "price": 2.99,
            "category": "Produce",
            "unit": "bunch",
            "image_url": "https://images.unsplash.com/photo-1571501478200-720616235bbf?q=80&w=2670&auto=format&fit=crop",
            "tags": ["fruit", "healthy", "snack"],
            "stock": 50,
            "lat": 28.6139, "lng": 77.2090  # Delhi coords approx
        },
        {
            "name": "Amul Taza Fresh Milk",
            "description": "Fresh pasteurized toned milk, rich in calcium and vitamins.",
            "price": 1.49,
            "category": "Dairy",
            "unit": "1L",
            "image_url": "https://images.unsplash.com/photo-1550583724-b2692b85b150?q=80&w=2787&auto=format&fit=crop",
            "tags": ["milk", "dairy", "breakfast"],
            "stock": 100,
            "lat": 28.6140, "lng": 77.2091
        },
        {
            "name": "Avocado Hass",
            "description": "Creamy, premium grade Hass avocado, perfect for guacamole or toast.",
            "price": 3.99,
            "category": "Produce",
            "unit": "piece",
            "image_url": "https://images.unsplash.com/photo-1523049673857-eb18f1d7b578?q=80&w=2586&auto=format&fit=crop",
            "tags": ["avocado", "healthy", "keto"],
            "stock": 30,
            "lat": 28.6145, "lng": 77.2100
        },
        {
            "name": "Lays Classic Potato Chips",
            "description": "Crispy, thinly sliced classic salted potato chips.",
            "price": 1.99,
            "category": "Snacks",
            "unit": "1 packet",
            "image_url": "https://images.unsplash.com/photo-1566478989037-e924e5ba03ef?q=80&w=2670&auto=format&fit=crop",
            "tags": ["chips", "potato", "salty"],
            "stock": 200,
            "lat": 28.6139, "lng": 77.2090
        },
        {
            "name": "Coca-Cola Zero Sugar",
            "description": "Zero sugar, same great Coca-Cola taste.",
            "price": 2.49,
            "category": "Beverages",
            "unit": "2L Bottle",
            "image_url": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?q=80&w=2670&auto=format&fit=crop",
            "tags": ["soda", "coke", "drink"],
            "stock": 120,
            "lat": 28.6142, "lng": 77.2095
        },
        {
            "name": "Whole Wheat Bread",
            "description": "Freshly baked 100% whole wheat bread loaf.",
            "price": 3.49,
            "category": "Bakery",
            "unit": "loaf",
            "image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?q=80&w=2672&auto=format&fit=crop",
            "tags": ["bread", "wheat", "breakfast"],
            "stock": 40,
            "lat": 28.6135, "lng": 77.2085
        },
        {
            "name": "Organic Tomatoes",
            "description": "Red, ripe, and juicy organic vine tomatoes.",
            "price": 4.99,
            "category": "Produce",
            "unit": "1 kg",
            "image_url": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?q=80&w=2540&auto=format&fit=crop",
            "tags": ["tomato", "veg", "salad", "fresh"],
            "stock": 80,
            "lat": 28.6139, "lng": 77.2090
        }
    ]

    print(f"📦 Uploading {len(products)} products and generating AI embeddings...")
    for idx, p in enumerate(products):
        res = requests.post(f"{BASE_URL}/products", json=p, headers=headers)
        if res.status_code == 201:
            print(f"  [+] Added: {p['name']}")
        else:
            print(f"  [-] Failed {p['name']}: {res.text}")

    print("🎉 Seeding complete!")

if __name__ == "__main__":
    seed()
