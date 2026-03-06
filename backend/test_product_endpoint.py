import requests

# We first register a mock seller to get a token.
res = requests.post("http://127.0.0.1:8000/auth/register", json={
    "name": "Test Seller",
    "email": "testseller99@example.com",
    "password": "password",
    "role": "seller",
    "lat": None,
    "lng": None
})

token = ""
if res.status_code == 200 or res.status_code == 201:
    token = res.json().get("access_token")
else:
    # If already exists, login
    res = requests.post("http://127.0.0.1:8000/auth/login", json={
        "email": "testseller99@example.com",
        "password": "password"
    })
    token = res.json().get("access_token")

headers = {"Authorization": f"Bearer {token}"}

payload = {
    'name': 'Test Item',
    'description': 'Description',
    'price': 99.0,
    'category': 'Fruits',
    'stock': 50,
    'unit': 'piece',
    'tags': ['a']
}

print("Testing min payload without optional fields...")
res = requests.post("http://127.0.0.1:8000/products", json=payload, headers=headers)
print(res.status_code, res.text)

print("\nTesting full payload with null fields...")
payload_full = {
    'name': 'Test Item 2',
    'description': 'Description 2',
    'price': 99.0,
    'mrp': None,
    'category': 'Fruits',
    'barcode': None,
    'stock': 50,
    'unit': 'piece',
    'image_url': None,
    'tags': ['a'],
    'lat': None,
    'lng': None,
    'address': 'Some Address'
}
res2 = requests.post("http://127.0.0.1:8000/products", json=payload_full, headers=headers)
print(res2.status_code, res2.text)
