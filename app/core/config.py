from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "AI Recruiter Copilot"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False
    OPENAI_API_KEY: str = ""
    JWT_SECRET: str = "test-secret-key-which-is-32-chars-long!"

    model_config = ConfigDict(env_file=".env", extra="ignore")


settings = Settings()
