import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Settings
    GEMINI_API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./candidate_screener.db"
    UPLOAD_DIR: str = "./data/uploads"
    KNOWLEDGE_BASE_DIR: str = "./knowledge_base"
    MAX_QUESTIONS: int = 5
    
    # Configuration priority: env vars > .env file
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Post-processing: Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
db_dir = os.path.dirname(settings.DATABASE_URL.replace("sqlite:///", ""))
if db_dir:
    os.makedirs(db_dir, exist_ok=True)
