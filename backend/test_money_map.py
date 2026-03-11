
import requests

BASE_URL = "http://localhost:8000"

def test_money_map():
    print("Testing /analytics/money-map...")
    try:
        resp = requests.get(f"{BASE_URL}/analytics/money-map?days=30")
        print(f"Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Error: {resp.text}")
        else:
            data = resp.json()
            print(f"Data points found: {len(data.get('data_points', []))}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_money_map()
