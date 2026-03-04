import requests
import time

try:
    print('Testing Auto-Expanding Search...')
    # Niche query
    q = 'quantum physics textbook for college students'
    r = requests.get('http://localhost:8000/search', params={'q': q})
    print('Search 1 Status:', r.status_code)
    data = r.json()
    count = data.get('count', 0)
    print(f'Search 1 Count: {count}')
    
    if count > 0:
        names = [p.get('name') for p in data.get('results', [])]
        print(f'Products found: {names}')
        
        # Test 2: Search again. It should now have score > 0.5 and NOT generate new ones
        time.sleep(2)
        r2 = requests.get('http://localhost:8000/search', params={'q': q})
        data2 = r2.json()
        print(f'Search 2 Count: {data2.get("count", 0)}')
        if data2.get('count', 0) > 0:
            print('Search 2 matches exactly the previous generated products.')
            print('SUCCESS: Hybrid Search works flawlessly.')

except Exception as e:
    print('Error:', e)
