import httpx
import json

import os

def test_direct():
    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        print("Error: CLAUDE_API_KEY not found in environment")
        return
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": "claude-3-5-sonnet-20240620",
        "max_tokens": 100,
        "messages": [{"role": "user", "content": "Hola"}]
    }
    
    with httpx.Client() as client:
        try:
            resp = client.post(url, headers=headers, json=payload, timeout=30.0)
            print(f"Status: {resp.status_code}")
            print(f"Body: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_direct()
