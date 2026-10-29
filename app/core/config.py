from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    
    # App
    APP_NAME: str = "AI Recruiter Copilot"
    VERSION: str = "2.0.0"

    # LLM (LiteLLM)
    LLM_PROVIDER: str = "anthropic"
    LLM_MODEL: str = "claude-sonnet-4-20250514"
    ANTHROPIC_API_KEY: Optional[str] = None

    # Embedding
    EMBEDDING_MODEL: str = "text-embedding-3-small"  # OpenAI via LiteLLM

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    COLLECTION_NAME: str = "cv_collection"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
