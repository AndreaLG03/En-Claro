import logging
from typing import Optional
from anthropic import AsyncAnthropic, APIError, APIStatusError
from ..config import settings

logger = logging.getLogger(__name__)

# Global client
_client: Optional[AsyncAnthropic] = None

def get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        if not settings.CLAUDE_API_KEY:
            raise ValueError("CLAUDE_API_KEY is not configured.")
        _client = AsyncAnthropic(api_key=settings.CLAUDE_API_KEY)
    return _client

async def close_client():
    global _client
    if _client:
        await _client.close()
        _client = None

async def call_claude(system_prompt: str, user_prompt: str) -> str:
    """
    Calls the Anthropic API using the official SDK.
    """
    client = get_client()
    
    try:
        message = await client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        # Content is a list of blocks, usually text.
        if message.content and len(message.content) > 0:
            return message.content[0].text
        return ""

    except APIStatusError as e:
        logger.error(f"Anthropic API Status Error: {e.status_code} - {e.message}")
        if e.status_code == 429:
             # SDK handles some retries, but if it bubbles up, we can log it.
             # In a real app we might want more complex backoff, 
             # but the SDK default is usually sufficient for standard usage.
             pass
        raise e
    except APIError as e:
        logger.error(f"Anthropic API Error: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error calling Claude: {str(e)}")
        raise e
