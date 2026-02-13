import os
# Set env var BEFORE importing app config
os.environ["CLAUDE_API_KEY"] = "sk-ant-dummy"

import asyncio
import logging
# Now import app modules
from app.api.routes import analyze_text
from app.models.schemas import TextRequest
from app.models.enums import AnalysisModule
from app.config import settings

# Force setting in case it was already loaded
settings.CLAUDE_API_KEY = "sk-ant-dummy"

logging.basicConfig(level=logging.INFO)

async def test_repro():
    print(f"Testing analyze_text with roleplay module. Key: {settings.CLAUDE_API_KEY}")
    
    # Mock history structure
    history = [
        {"role": "system", "content": "Escenario: Conflicto"},
        {"role": "user", "content": "Hola"}
    ]
    
    import json
    text_payload = json.dumps(history)
    
    req = TextRequest(
        text=text_payload,
        module=AnalysisModule.ROLEPLAY
    )
    
    try:
        await analyze_text(req)
        print("Success (Unexpected with dummy key)")
    except Exception as e:
        # We want to see if this is a 500 or 400
        # In FastAPI, HTTPException is an exception, but let's see what analyze_text raises
        print(f"Caught Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_repro())
