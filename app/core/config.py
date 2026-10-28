from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "AI Recruiter Copilot"
    debug: bool = True
    log_level: str = "INFO"

    # APIs
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # ChromaDB
    chroma_persist_dir: str = "./chroma_db"

    class Config:
        env_file = ".env"


settings = Settings()
