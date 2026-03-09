import requests
import json

BASE_URL = "http://localhost:8000"

def test_profile_update():
    # First, we need a token. Let's assume there's a test user.
    # We'll try to login as 'virat@email.com' if it exists, or just use a dummy login to see the error.
    
    login_data = {"email": "virat@email.com", "password": "password123"} # Dummy creds
    try:
        res = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if res.status_code == 200:
            token = res.json()["access_token"]
            print(f"Login successful. Token: {token[:10]}...")
            
            # Test PUT /user/profile
            update_data = {
                "name": "Virat Kohli Updated",
                "profile_image": "https://picsum.photos/200"
            }
            headers = {"Authorization": f"Bearer {token}"}
            put_res = requests.put(f"{BASE_URL}/user/profile", json=update_data, headers=headers)
            print(f"PUT /user/profile status: {put_res.status_code}")
            print(f"Response: {put_res.text}")
        else:
            print(f"Login failed: {res.status_code} {res.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_profile_update()
