import httpx
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)
CLAUDE_URL = "https://api.anthropic.com/v1/messages"

# Global client for connection pooling
_client: Optional[httpx.AsyncClient] = None

def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=90.0)
    return _client

async def close_client():
    global _client
    if _client:
        await _client.aclose()
        _client = None

async def call_claude(system_prompt: str, user_prompt: str) -> str:
    """
    Calls the Anthropic API with provided prompts.
    Uses a pooled AsyncClient for efficiency with simple retry logic.
    """
    if not settings.CLAUDE_API_KEY:
        raise ValueError("CLAUDE_API_KEY is not configured.")

    headers = {
        "x-api-key": settings.CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    payload = {
        "model": settings.CLAUDE_MODEL,
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_prompt}
        ]
    }

    client = get_client()
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await client.post(CLAUDE_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                logger.warning(f"Rate limited. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                import asyncio
                await asyncio.sleep(wait_time)
                continue
            logger.error(f"Anthropic API error: {e.response.status_code} - {e.response.text}")
            raise
        except (httpx.RequestError, Exception) as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 1
                logger.warning(f"Request error: {str(e)}. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                import asyncio
                await asyncio.sleep(wait_time)
                continue
            logger.error(f"Unexpected error calling Claude: {str(e)}")
            raise
    return "" # Should not reach here
