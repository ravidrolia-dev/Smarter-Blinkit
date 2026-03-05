import requests
import base64
import time

def test_api():
    # Read a sample image
    with open(r"C:\Users\RAVI0\.gemini\antigravity\brain\8fa89686-2e90-43c6-a052-ab9986ac43b1\media__1772737399230.png", "rb") as f:
        img_data = f.read()
    
    encoded = base64.b64encode(img_data).decode('utf-8')
    payload = "data:image/jpeg;base64," + encoded

    print(f"Payload size: {len(payload)/1024:.2f} KB")

    # Send request
    try:
        start_time = time.time()
        res = requests.post("http://localhost:8000/inventory/scan", 
                            json={"image_base64": payload}, 
                            headers={"Authorization": "Bearer fake_token_just_testing"}) # Token might be invalid if protected
        end_time = time.time()
        
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.text}")
        print(f"Time Taken: {end_time - start_time:.2f} seconds")
    except Exception as e:
        print(f"Network Error: {e}")

if __name__ == "__main__":
    test_api()
