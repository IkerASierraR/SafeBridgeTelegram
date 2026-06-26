from pydantic_settings import BaseSettings
import os
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "SafeBridge Telegram API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Directorio temporal para backups antes de enviarlos
    TEMP_DIR: str = os.getenv("TEMP_DIR", "/tmp/safebridge_backups")

    class Config:
        case_sensitive = True

settings = Settings()

# Ensure temp directory exists
Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)
