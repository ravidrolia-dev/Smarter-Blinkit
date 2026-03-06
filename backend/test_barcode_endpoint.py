import requests
import sys

try:
    # We will use test_product_endpoint.py as reference
    res = requests.post("http://127.0.0.1:8000/auth/login", json={"email": "testseller99@example.com", "password": "password"}, timeout=5)
    token = res.json().get("access_token")
    if not token:
        print("Login failed, trying register")
        res = requests.post("http://127.0.0.1:8000/auth/register", json={"name": "Test", "email": "testseller99@example.com", "password": "password", "role": "seller"}, timeout=5)
        res = requests.post("http://127.0.0.1:8000/auth/login", json={"email": "testseller99@example.com", "password": "password"}, timeout=5)
        token = res.json().get("access_token")
    
    print(f"Got token: {token[:10]}...")
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.post("http://127.0.0.1:8000/inventory/generate-barcode", headers=headers, timeout=5)
    print("Status:", res.status_code)
    print("Response:", res.text)
except Exception as e:
    print(f"Script Error: {e}")
