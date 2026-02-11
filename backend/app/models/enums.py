from enum import Enum

class AnalysisModule(str, Enum):
    MESSAGE = "message"
    AUDIO = "audio"
    GLOSSARY = "glossary"
    RESPONSE = "response"
    ROUTINE = "routine"
    DECODER = "decoder"
    ROLEPLAY = "roleplay"
    ROLEPLAY_FEEDBACK = "roleplay_feedback"
    TRANSLATOR = "translator"
