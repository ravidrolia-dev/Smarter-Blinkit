"""
Script to check all product image URLs and identify broken links.
"""
import requests
from pymongo import MongoClient
from urllib.parse import urlparse

def check_url(url, timeout=5):
    """Check if URL returns 200 status code."""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except:
        try:
            # Try GET if HEAD fails
            response = requests.get(url, timeout=timeout, stream=True)
            return response.status_code == 200
        except:
            return False

def main():
    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    db = client["smarter_blinkit"]
    
    print("\n" + "="*70)
    print("🔍 CHECKING PRODUCT IMAGE URLS")
    print("="*70)
    
    products = list(db.products.find({}))
    
    broken_urls = []
    working_urls = []
    
    for i, product in enumerate(products, 1):
        name = product.get("name", "Unknown")
        image_url = product.get("image_url", "")
        product_id = str(product.get("_id"))
        
        print(f"\n[{i}/{len(products)}] Testing: {name}")
        print(f"   URL: {image_url[:80]}...")
        
        if not image_url:
            print("   ❌ NO URL")
            broken_urls.append({
                "id": product_id,
                "name": name,
                "url": image_url,
                "reason": "Missing URL"
            })
            continue
        
        is_working = check_url(image_url)
        
        if is_working:
            print("   ✅ WORKING")
            working_urls.append({
                "id": product_id,
                "name": name,
                "url": image_url
            })
        else:
            print("   ❌ BROKEN")
            broken_urls.append({
                "id": product_id,
                "name": name,
                "url": image_url,
                "reason": "URL not accessible"
            })
    
    # Summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    print(f"✅ Working URLs: {len(working_urls)}/{len(products)}")
    print(f"❌ Broken URLs:  {len(broken_urls)}/{len(products)}")
    
    if broken_urls:
        print("\n" + "="*70)
        print("❌ PRODUCTS WITH BROKEN IMAGE LINKS:")
        print("="*70)
        for item in broken_urls:
            print(f"\n• {item['name']}")
            print(f"  ID: {item['id']}")
            print(f"  Reason: {item['reason']}")
            if item['url']:
                print(f"  URL: {item['url']}")
    
    client.close()
    
    return broken_urls

if __name__ == "__main__":
    broken = main()
    
    if broken:
        print("\n" + "="*70)
        print(f"⚠️  Found {len(broken)} products with broken images")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("🎉 All product images are working!")
        print("="*70)
