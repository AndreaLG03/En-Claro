from pydantic import BaseModel

class TextRequest(BaseModel):
    text: str
    module: str
    user_profile: dict = {} # e.g. {"name": "Andrea", "gender": "femenino"}
    user_email: str | None = None # For premium checks
    scenario_context: dict = {} # e.g. {"character_name": "Sofía", "role": "Amiga"}

class AIResponse(BaseModel):
    result: str
