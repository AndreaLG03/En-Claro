from pydantic import BaseModel

class TextRequest(BaseModel):
    text: str
    module: str

class AIResponse(BaseModel):
    result: str
