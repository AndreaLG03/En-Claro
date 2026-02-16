import requests
import sys

url = "https://en-claro.onrender.com/api/history"
email = "test@example.com"

try:
    print(f"Testing {url} with email={email}...")
    r = requests.get(url, params={"email": email}, timeout=10)
    print(f"Status Code: {r.status_code}")
    print(f"Response Headers: {r.headers}")
    print(f"Response Body: {r.text[:500]}") # First 500 chars
except Exception as e:
    print(f"Request failed: {e}")
