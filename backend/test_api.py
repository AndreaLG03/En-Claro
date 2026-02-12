import httpx
import json
import asyncio

async def test_analyze():
    url = "http://127.0.0.1:8001/api/analyze"
    payload = {
        "text": "Hola, ¿cómo estás?",
        "module": "message"
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=90.0)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
        except Exception as e:
            print(f"Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_analyze())
