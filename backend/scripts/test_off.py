import requests
url = "https://in.openfoodfacts.org/api/v2/search?categories_tags_en=shampoo&fields=code,product_name,brands,image_url,categories&page_size=5"
print("Trying URL:", url)
try:
    r = requests.get(url, headers={"User-Agent": "SmarterBlinkIt"}, timeout=10)
    print("Status:", r.status_code)
    print("Data length:", len(r.content))
    print(r.json().get("products", [])[:1])
except Exception as e:
    print("Error:", e)
