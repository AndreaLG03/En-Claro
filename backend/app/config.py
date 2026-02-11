from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional

BACKEND_ROOT = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    CLAUDE_API_KEY: str
    CLAUDE_MODEL: str = "claude-sonnet-4-5"
    
    # Environment file configuration
    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()

# Export for convenience, though using 'settings' object is preferred
CLAUDE_API_KEY = settings.CLAUDE_API_KEY
CLAUDE_MODEL = settings.CLAUDE_MODEL
