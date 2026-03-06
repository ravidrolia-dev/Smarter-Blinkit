import requests
r = requests.get('https://dummyjson.com/products?limit=100')
data = r.json()
if 'products' in data:
    for p in data['products']:
        print(f"{p['id']}: {p['title']} | Category: {p['category']}")
else:
    print(f"Data received: {list(data.keys())}")
    if isinstance(data, list):
        print(f"Total products: {len(data)}")
