import requests
import json

def test():
    url = "http://localhost:8000/orders/estimate"
    payload = {
        "items": [],
        "delivery_address": "Jaipur",
        "buyer_lat": 26.9124,
        "buyer_lng": 75.7873
    }
    r = requests.post(url, json=payload)
    print(json.dumps(r.json(), indent=2))

if __name__ == "__main__":
    test()
