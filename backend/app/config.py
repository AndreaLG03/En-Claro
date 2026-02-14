from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional

BACKEND_ROOT = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    CLAUDE_API_KEY: Optional[str] = None # Optional to prevent startup crash if env var missing
    CLAUDE_MODEL: str = "claude-sonnet-4-5-20250929" # Updated to Claude Sonnet 4.5 (Sep 2025)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    SECRET_KEY: str = "secret-key-for-dev"
    RENDER: bool = False # Render sets this automatically
    DATABASE_URL: Optional[str] = None
    
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
GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET
SECRET_KEY = settings.SECRET_KEY
render_env = settings.RENDER
