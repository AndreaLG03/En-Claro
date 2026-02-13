import os
os.environ["CLAUDE_API_KEY"] = "sk-ant-dummy"
import asyncio
from app.api.routes import analyze_text
from app.models.schemas import TextRequest
from app.models.enums import AnalysisModule
from app.config import settings

settings.CLAUDE_API_KEY = "sk-ant-dummy"

async def test_repro():
    print("Testing analyze_text with roleplay module and BRACES in content...")
    
    # JSON string naturally contains braces!
    # "{\"role\": ...}"
    history = [{"role": "user", "content": "Hola"}]
    import json
    text_payload = json.dumps(history) # This string has { and }
    
    req = TextRequest(text=text_payload, module=AnalysisModule.ROLEPLAY)
    
    try:
        await analyze_text(req)
        print("Success") # Should fail if format is used blindly
    except Exception as e:
        print(f"Caught Exception: {type(e).__name__}: {e}")
        # import traceback
        # traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_repro())
